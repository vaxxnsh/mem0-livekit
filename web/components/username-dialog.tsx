import React, { SetStateAction } from 'react';
import { User } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogOverlay,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

interface UsernameDialogProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<SetStateAction<boolean>>;
  username: string;
  setUsername: React.Dispatch<SetStateAction<string>>;
  startCall: React.Dispatch<SetStateAction<boolean>>;
}

const UsernameDialog = ({
  isOpen,
  setIsOpen,
  username,
  setUsername,
  startCall,
}: UsernameDialogProps) => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-4">
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogOverlay className="bg-black/40 backdrop-blur-sm fixed inset-0" />
        <DialogContent className="sm:max-w-md bg-white/90 border-0 shadow-2xl rounded-2xl">
          <DialogHeader className="space-y-3 pb-2">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-md">
                <User className="h-6 w-6 text-white" />
              </div>
              <div>
                <DialogTitle className="text-xl font-bold text-gray-900">
                  Enter Username
                </DialogTitle>
                <DialogDescription className="text-gray-600 text-sm">
                  Choose your unique identifier
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label
                htmlFor="username"
                className="text-sm font-medium text-gray-700"
              >
                Username
              </Label>
              <Input
                id="username"
                type="text"
                placeholder="johndoe123"
                value={username}
                onChange={(e) => setUsername(e.target.value.trim())}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && username.trim()) {
                    startCall(true);
                    setIsOpen(false);
                  }
                }}
                className="h-12 px-4 border-2 border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 rounded-xl transition-all duration-200 text-base"
                autoFocus
              />
              <p className="text-xs text-gray-500 mt-1">
                Must be 3-20 characters, letters and numbers only
              </p>
            </div>
          </div>

          <DialogFooter className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsOpen(false)}
              className="flex-1 h-12 rounded-xl border-2 hover:bg-gray-50 font-medium"
            >
              Cancel
            </Button>
            <Button
              type="button"
              disabled={!username.trim()}
              onClick={() => {
                if (username.trim()) {
                  startCall(true);
                  setIsOpen(false);
                } else {
                  toast.warning('Enter a valid username');
                }
              }}
              className="flex-1 h-12 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50"
            >
              Start Call
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UsernameDialog;