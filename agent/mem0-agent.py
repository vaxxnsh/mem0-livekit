import asyncio
import base64
import json
from mem0 import AsyncMemoryClient
from livekit import agents, rtc
from livekit.agents import (
    WorkerOptions,
    cli,
    ChatContext,
    ChatMessage,
    RoomInputOptions,
    Agent,
    AgentSession,
    get_job_context
)
from livekit.agents.llm import ImageContent
from livekit.plugins import openai, silero, deepgram,cartesia, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from config import logger
from utils import frame_to_base64


class MemoryEnabledAgent(Agent):
    def __init__(self, user_id: str) -> None:
        self._latest_frame = None
        self._video_stream = None
        self._tasks = []  # Prevent garbage collection of running tasks
        self._user_id = user_id or "default"
        self._mem0_client = AsyncMemoryClient()
        super().__init__(
            instructions="""
                You are Maria, a helpful voice and vision assistant with memory capabilities.
                Use past interactions to provide contextually relevant responses.
                If no relevant context is available, rely on your general knowledge.
            """
        )
        logger.info(f"Mem0 Agent initialized. Using user_id: {self._user_id}")
    
    async def on_enter(self):
        ctx = get_job_context()
        room = ctx.room
        
        logger.info(f"Room Name: {ctx.room.name}")
        
        self._user_id = ctx.room.name.split("-")[1]
        
        logger.info(f"user_id set to : {self._user_id}")
            
        def _image_received_handler(reader, participant_identity):
            task = asyncio.create_task(
                self._image_received(reader, participant_identity)
            )
            self._tasks.append(task)
            task.add_done_callback(lambda t: self._tasks.remove(t))
            
        room.register_byte_stream_handler("images", _image_received_handler)
        
        logger.info(f"Number of participants: {len(room.remote_participants.values())}")
        
        # Log initial participants 
        for participant in room.remote_participants.values():
            logger.info(f"Initial participant connected: {participant.identity}")

    
        for participant in room.remote_participants.values():
            video_tracks = [
                publication.track for publication in participant.track_publications.values() 
                if publication.track and publication.track.kind == rtc.TrackKind.KIND_VIDEO
            ]
            
            if video_tracks:
                self._create_video_stream(video_tracks[0])
                break
            
        @room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                self._create_video_stream(track)
        
        # Log new participant connections
        
        def on_participant_connected(participant: rtc.RemoteParticipant):
            logger.info(f"Participant connected: {participant.identity}")
            
        room.on("participant_connected",on_participant_connected)
        


    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        user_id = self._user_id
        user_text = new_message.text_content
        
        
        
        logger.info(f"""
                After User turn : user_id={user_id} user_text={user_text}
        """)
        
        # Storing incoming in mem0 to be looked up later
        
        await self.store_to_memory(user_id,user_text)
        
        # Adding Latest Frame to content
        
        if self._latest_frame:
            if isinstance(new_message["content"], list):
                new_message["content"].append(ImageContent(image=self._latest_frame))
            else:
                new_message["content"] = [new_message["content"], ImageContent(image=self._latest_frame)]
            
            self._latest_frame = None
        
        # Checking Rag Store and updating chat context 
        
        await self.adding_rag_lookup(
            user_id=user_id,
            query=user_text,
            turn_ctx=turn_ctx
        )
        
        await super().on_user_turn_completed(turn_ctx, new_message)
    
    async def adding_rag_lookup(self, query: str, user_id: str,turn_ctx : ChatContext):
        try:
            logger.info(f"Searching Mem0 for context: {query}")
            
            search_results = await self._mem0_client.search(
                query=query,
                user_id=user_id,
                limit=3  # Limit to 3 results to avoid overwhelming context
            )
            
            logger.info(f"Mem0 search results: {search_results} for query {query}")
            
            context_parts = []
            for result in search_results: 
                paragraph = result.get("memory") or result.get("text") or ""

                if paragraph:
                    source = result.get("source", "Mem0 Memories")
                    context_parts.append(f"Source: {source}\nContent: {paragraph}\n")
        
            if context_parts:
                full_context = "\n".join(context_parts)
                
                logger.info(f"Injecting RAG context: {full_context}")
                
                turn_ctx.add_message(
                    role="system",
                    content=f"Relevant past context:\n{full_context}"
                )
                
                await self.update_chat_ctx(turn_ctx)
            else:
                logger.info("No relevant context found for current message.")
        except Exception as e:
            logger.warning(f"Failed to retrieve RAG context: {e}")
    
    async def store_to_memory(self, user_id: str,text : str | None):
        if not text:
            logger.warning("No message to store in mem0")
            return
        
        try:
            logger.info(f"Storing user message: {text}")
            
            add_result = await self._mem0_client.add(
                [{"role": "user", "content": text}],
                user_id=user_id
            )
            
            logger.info(f"Mem0 add result: {add_result}")    
        except Exception as e:
            logger.warning(f"Failed to store message in Mem0: {e}")
    
    def _create_video_stream(self, track: rtc.Track):
        if self._video_stream is not None:
            self._video_stream.close()
            
        self._video_stream = rtc.VideoStream(track)
        
        async def read_stream():
            async for event in self._video_stream:
                self._latest_frame = frame_to_base64(event.frame)

                
        task = asyncio.create_task(read_stream())
        self._tasks.append(task)
        task.add_done_callback(lambda t: self._tasks.remove(t) if t in self._tasks else None)

    async def _image_received(self, reader, participant_identity):
        image_bytes = bytes()
        
        async for chunk in reader:
            image_bytes += chunk

        chat_ctx = self.chat_ctx.copy()
        
        chat_ctx.add_message(
            role="user",
            content=[
                "Here's an image I want to share with you:",
                ImageContent(
                    image=f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
                )
            ],
        )
        
        await self.update_chat_ctx(chat_ctx)

# --- LiveKit Entrypoint ---

async def entrypoint(ctx: agents.JobContext):
 
    user_id = "default"
    
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=MemoryEnabledAgent(
            user_id=user_id  
        ),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            video_enabled=True,
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and let them know you can analyze images they share or their camera feed."
    )



if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))