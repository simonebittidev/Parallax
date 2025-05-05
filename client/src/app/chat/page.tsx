
import { Suspense } from 'react';
import ChatContent from '@/components/chat';
import Navbar from '@/components/navbar';


export default function ChatPage() {
  return (
    <Suspense fallback={<div>Caricamento chat...</div>}>
      <>
      <Navbar />
      <ChatContent />
      </>
    </Suspense>
  );
}