'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import clsx from 'clsx';
import { onAuthStateChanged, User } from 'firebase/auth'
import { logOut, auth } from '../lib/firebase'
import { PlusIcon } from '@heroicons/react/24/solid';

type ChatMessage = {
  role: 'user' | 'ai';
  agent_name: 'Opposite' | 'Neutral' | 'Emphatic';
  content: string;
};

const ChatContent = () => {
  const params = useSearchParams();
  const chatBoxRef = useRef<HTMLDivElement>(null);
  const perspective = params.get('perspective') as ChatMessage['agent_name'] | null;
  const conv_id = params.get('conv_id') as string || null;
  const [activePerspectives, setActivePerspectives] = useState<string[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user: User | null) => {
      if (user) {
        setUserId(user.uid); // ✅ Ottieni l'ID utente loggato
      } else {
        setUserId(null);
      }
    });

    return () => unsubscribe(); // Cleanup
  }, []);

  const getMessages = async () => {
    try {

      console.log('conv_id:', conv_id);
      console.log('userId:', userId); 

      if (!userId || !conv_id) {
        alert('si è verificato un errore');
        return;
      }

      const user_id = userId;
      const url = `/messages/${user_id}/${conv_id}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
  
      if (!response.ok) {
        throw new Error('Errore nella risposta del server');
      }
  
      const messages = JSON.parse(await response.json());
      console.log('Messaggi ricevuti:', messages);

      if (Array.isArray(messages)) {
        console.log('messaggi ricevuti in formato array');
        setChatMessages(messages);
      }

    } catch (error) {
      console.error('Errore durante la chiamata al server:', error);
      alert('Si è verificato un errore durante la comunicazione con il server.');
    }
  };

  useEffect(() => {
    if (userId && conv_id) {
      getMessages();
    }
  }, [userId, conv_id]);
  
  // WB

  //initialize wbsocket
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/${userId}/${conv_id}`);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log("✅ WebSocket connesso");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const messages = JSON.parse(data);
        if (Array.isArray(messages)) {
          console.log('messaggi ws ricevuti in formato array');
          setChatMessages(messages);
        }else{
          console.log('messaggi ws non ricevuti in formato array');
          console.log(messages);
        }
      } catch (err) {
        console.error("Errore parsing messaggio:", err);
      }
    };

    socket.onclose = () => {
      console.log("❌ WebSocket disconnesso");
    };

    return () => {
      socket.close();
    };
  }, [userId, conv_id]);

  // END WB

  useEffect(() => {
    if (perspective) {
      setActivePerspectives([perspective]);
    }
  }, [perspective]);

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const handleSend = () => {
    if (!chatInput.trim()) return;

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ text: chatInput }));
      setChatInput("");
    }
  };

  const handle_new_pov = async (perspective:string) =>  {
      const response = await fetch('/api/processpov', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          perspective: perspective,
          userText: chatMessages[0].content,
          userId: userId,
          convId: conv_id,
        }),
      });

      if (!response.ok) {
        throw new Error('Errore nella risposta del server');
      }

      await getMessages();
  };

  return (
      <div className="flex flex-col h-screen max-w-3xl mx-auto pt-15">
        <div className="flex-1 overflow-y-auto p-4" ref={chatBoxRef}>
          {chatMessages.map((msg, i) => (
            <div key={i} className={`mb-5 flex items-start gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role !== 'user' && (
                <div
                  className={clsx(
                    'w-8 h-8 flex items-center mt-1 justify-center rounded-full text-white font-bold text-sm',
                    {
                      'bg-red-500': msg.agent_name === 'Opposite',
                      'bg-blue-500': msg.agent_name === 'Neutral',
                      'bg-green-500': msg.agent_name === 'Emphatic',
                    }
                  )}
                >
                  {msg.agent_name[0]}
                </div>
              )}
              <div
                className={`rounded-xl px-5 py-3 text-sm max-w-[80%] whitespace-pre-line ${msg.role === 'user' ? 'bg-black text-white' : 'bg-gray-100 text-black'}`}
              >
                {msg.content}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 bg-white">
          <a href="/" className="">
            <span aria-hidden="true" className='mr-1'>&larr;</span>
            Genera una nuova prospettiva
          </a>
          <div tabIndex={0} className="mt-2 flex gap-2 border p-2 rounded-2xl border-gray-300 bg-gray-100 h-20 focus-within:ring-2 focus-within:ring-indigo-600 focus-within:outline-none">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Write your message..."
              className="flex-1 hover:bg-gray-100 focus:outline-none"
            />
            <button
              onClick={handleSend}
              className="bottom-3 right-3 w-10 h-10 bg-indigo-600 text-white rounded-full flex items-center justify-center hover:bg-indigo-600-dark"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>
          <div>
            {['Opposite', 'Neutral', 'Emphatic']
            .filter(p => !chatMessages.some(msg => msg.agent_name === p))
            .map(p => (
              <button
              key={p}
              onKeyDown={(e) => e.key === 'Enter' && handle_new_pov(p)}
              onClick={() => handle_new_pov(p)}
              className="mt-2 inline-flex items-center px-6 py-2 bg-gray-100 rounded-xl border border-gray-300 hover:bg-gray-200 transition mr-2"
              >
              <PlusIcon className="size-5 mr-2"/> {p}
              </button>
            ))}
          </div>
        </div>
      </div>
  );
};

export default ChatContent;