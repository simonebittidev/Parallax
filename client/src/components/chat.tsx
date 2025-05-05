'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import clsx from 'clsx';

type ChatMessage = {
  from: 'user' | 'Opposto' | 'Neutrale' | 'Empatico';
  text: string;
};

const ChatContent = () => {
  const params = useSearchParams();
  const chatBoxRef = useRef<HTMLDivElement>(null);
  const perspective = params.get('perspective') as ChatMessage['from'] | null;
  const [activePerspectives, setActivePerspectives] = useState<string[]>([]);

  const userText = params.get('userText');
  const rewritten = params.get('rewritten');

  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

  useEffect(() => {
    if (perspective) {
      setActivePerspectives([perspective]);
    }
  }, [perspective]);

  useEffect(() => {
    if (perspective && userText && rewritten) {
      setChatMessages([
        { from: 'user', text: userText },
        { from: perspective, text: rewritten },
      ]);
    }
  }, [perspective, userText, rewritten]);

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const handleSend = () => {
    if (!chatInput.trim() || !perspective) return;

    const newMessages: ChatMessage[] = [
      ...chatMessages,
      { from: 'user', text: chatInput.trim() },
      {
        from: perspective,
        text: `${chatInput.trim()}`
      }
    ];

    setChatMessages(newMessages);
    setChatInput('');
  };

  return (
    
      <div className="flex flex-col h-screen max-w-3xl mx-auto py-5 pt-15">
        <div className="flex-1 overflow-y-auto p-4" ref={chatBoxRef}>
          {chatMessages.map((msg, i) => (
            <div key={i} className={`mb-5 flex items-start gap-2 ${msg.from === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.from !== 'user' && (
                <div
                  className={clsx(
                    'w-8 h-8 flex items-center mt-1 justify-center rounded-full text-white font-bold text-sm',
                    {
                      'bg-red-500': msg.from === 'Opposto',
                      'bg-blue-500': msg.from === 'Neutrale',
                      'bg-green-500': msg.from === 'Empatico',
                    }
                  )}
                >
                  {msg.from[0]}
                </div>
              )}
              <div
                className={`rounded-xl px-5 py-3 text-sm max-w-[80%] whitespace-pre-line ${msg.from === 'user' ? 'bg-black text-white' : 'bg-gray-100 text-black'}`}
              >
                {msg.text}
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
            {['Opposto', 'Neutrale', 'Empatico'].filter(p => p !== perspective && !activePerspectives.includes(p)).map(p => (
              <button
                key={p}
                onClick={() => {
                  setChatMessages(prev => [
                    ...prev,
                    {
                      from: p as ChatMessage['from'],
                      text: `${rewritten}`,
                    }
                  ]);
                  setActivePerspectives(prev => [...prev, p]);
                }}
                className="mt-2 inline-flex items-center px-6 py-2 bg-gray-100 rounded-xl border border-gray-300 hover:bg-gray-200 transition mr-2"
              >
                ➕ Aggiungi {p}
              </button>
            ))}
          </div>
        </div>
      </div>
  );
};

export default ChatContent;