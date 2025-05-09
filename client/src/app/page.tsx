'use client'

import { useState, useEffect, useRef} from 'react'
import Navbar from '@/components/navbar';
import clsx from 'clsx';
import { useRouter } from 'next/navigation';
import { onAuthStateChanged, User } from 'firebase/auth'
import { logOut, auth } from '../lib/firebase'
import { ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';

export default function Home() {
  const [userId, setUserId] = useState<string | null>(null);
  const router = useRouter();
  
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


  // Tipi TypeScript
  interface ChatMessage {
    from: 'user' | 'Opposite' | 'Neutral' | 'Emphatic';
    text: string;
  }

  const [selectedPerspective, setSelectedPerspective] = useState<'Opposite' | 'Neutral' | 'Emphatic' | null>(null);
  const [inputText, setInputText] = useState<string>('');
  const [rewrittenText, setRewrittenText] = useState<string>('');
  const [conv_id, setConvId] = useState<string>('');
  const [showResponse, setShowResponse] = useState<boolean>(false);
  const [inChat, setInChat] = useState<boolean>(false);
  const [chatInput, setChatInput] = useState<string>('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const activeAgents = useRef<Set<'Opposite' | 'Neutral' | 'Emphatic'>>(new Set());
  const chatBoxRef = useRef<HTMLDivElement>(null);

  const handlePerspectiveClick = (perspective: 'Opposite' | 'Neutral' | 'Emphatic') => {
    setSelectedPerspective(perspective);
  };

  const handleChatStart = () => {
    if (!selectedPerspective) return;
    const params = new URLSearchParams({
      conv_id:conv_id
    });
    router.push(`/chat?${params.toString()}`);
  };

  const handleSubmit = async () => {
    if (!inputText || !selectedPerspective) {
      alert('Per favore, inserisci un testo e seleziona una prospettiva.');
      return;
    }

    try {
      const response = await fetch('/api/processpov', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          perspective: selectedPerspective,
          userText: inputText,
          userId: userId
        }),
      });

      if (!response.ok) {
        throw new Error('Errore nella risposta del server');
      }

      const data = await response.json();
      setRewrittenText(data.pov);
      setConvId(data.conv_id);

      setShowResponse(true);
    } catch (error) {
      console.error('Errore durante la chiamata al server:', error);
      alert('Si è verificato un errore durante la comunicazione con il server.');
    }
  };

  const handleReset = () => {
    activeAgents.current.clear();
    setInChat(false);
    setShowResponse(false);
    setInputText('');
    setRewrittenText('');
    setConvId('');
    setSelectedPerspective(null);
    setChatMessages([]);
  };

  const handleChatSend = () => {
    if (!chatInput.trim()) return;
    const newMessages: ChatMessage[] = [
      ...chatMessages,
      { from: 'user', text: chatInput.trim() },
    ];

    activeAgents.current.forEach(agent => {
      const reply = `[Mock] ${agent}: Risposta ${
        agent === 'Opposite' ? 'contraria e provocatoria' :
        agent === 'Neutral' ? 'oggettiva e bilanciata' :
        'comprensiva e solidale'} → ${chatInput.trim()}`;
      newMessages.push({ from: agent, text: reply });
    });

    setChatMessages(newMessages);
    setChatInput('');
  };

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const perspectiveStyles: Record<'Opposite' | 'Neutral' | 'Emphatic', string> = {
    Opposite: 'bg-red-100 text-red-800',
    Neutral: 'bg-blue-100 text-blue-800',
    Emphatic: 'bg-green-100 text-green-800'
  };

  return (
    <div className="bg-white">
      <Navbar></Navbar>
      <div className="relative isolate pt-20 px-5">
        <div className="mx-auto max-w-2xl py-15">
          {/* <h1 className="text-4xl font-bold tracking-tight text-indigo-600">Parallax</h1> */}
            <p className="mt-2 text-lg text-neutral-600 font-bold">Reflect. Rephrase. Understand.</p>
            <p id="headerDescription" className="mt-4 text-base text-neutral-500">
            Parallax is an app for reflection and dialogue. Enter a thought, an opinion, or a short text,
            and Parallax will rewrite it from three different perspectives — opposing, neutral, and empathetic. It helps to explore nuances,
            gain clarity, and prepare for complex discussions.
            </p>
        </div>
      </div>
      <div className="relative isolate px-5">
      <div className="mx-auto max-w-2xl py-5">
      {!inChat && (
        <section id="mainSection">
          <div className="flex justify-center mt-4">
            <div className="inline-flex bg-gray-100 rounded-full p-1 gap-1 backdrop-blur-sm">
              {(['Opposite', 'Neutral', 'Emphatic'] as const).map(p => (
                <button
                  key={p}
                  onClick={() => handlePerspectiveClick(p)}
                  className={clsx(
                    'toggle-btn px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 focus:outline-none',
                    selectedPerspective === p && 'bg-indigo-600 text-white'
                  )}
                  style={selectedPerspective === p ? {
                    boxShadow: p === 'Opposite' ? '0 0 10px 3px rgba(239, 68, 68, 0.4)' :
                               p === 'Neutral' ? '0 0 10px 3px rgba(59, 130, 246, 0.4)' :
                                                  '0 0 10px 3px rgba(34, 197, 94, 0.4)'
                  } : {}}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 relative">
            <textarea
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              rows={4}
              placeholder="Write here your opinion..."
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              className="w-full pr-14 pl-4 py-3 border border-gray-200 bg-gray-100 rounded-2xl focus:outline-none focus:ring-2 focus:ring-indigo-600"
            />
            <button onClick={handleSubmit} className="absolute bottom-3 right-3 w-10 h-10 bg-indigo-600 text-white rounded-full flex items-center justify-center hover:bg-indigo-600-dark">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>

          {showResponse && (
            <div className="mt-6 p-6 rounded-2xl bg-indigo-600/5 text-neutral-800">
              <p className="text-base mb-4 leading-relaxed">{rewrittenText}</p>
                <button onClick={handleChatStart} className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-600-dark transition">
                <ChatBubbleLeftRightIcon className="h-5 w-5" />
                Chat with this perspective
                <svg xmlns="http://www.w3.org/2000/svg" className="ml-2 h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10.293 15.707a1 1 0 010-1.414L13.586 11H4a1 1 0 110-2h9.586l-3.293-3.293a1 1 0 111.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
                </button>
            </div>
          )}
        </section>
      )}

      {inChat && (
        <section className="flex flex-col h-[70vh] border rounded-xl bg-white shadow-sm">
          <div ref={chatBoxRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {chatMessages.map((msg, idx) => (
              <div key={idx} className={msg.from === 'user' ? 'flex justify-end' : 'flex justify-start'}>
                <div className={clsx(
                  'text-sm rounded-full px-4 py-2 whitespace-pre-line inline-block max-w-[80%]',
                  msg.from === 'user' ? 'text-black bg-white border' : perspectiveStyles[msg.from as keyof typeof perspectiveStyles] || 'bg-gray-200 text-black'
                )}>
                  {msg.text}
                </div>
              </div>
            ))}
          </div>
          <div className="p-4 border-t bg-white">
            <div className="relative">
              <input
                type="text"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Scrivi un messaggio..."
                className="w-full pr-12 pl-4 py-3 rounded-full border border-neutral-300 focus:ring-indigo-600 focus:outline-none"
              />
              <button onClick={handleChatSend} className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-indigo-600 text-white rounded-full flex items-center justify-center hover:bg-indigo-600-dark">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </button>
            </div>
            <div className="text-left mt-2">
              <button onClick={handleReset} className="px-4 py-2 bg-gray-100 text-indigo-600 rounded-full hover:bg-gray-200">Genera un nuovo punto di vista</button>
            </div>
          </div>
        </section>
      )}
    </div>
    </div>

    </div>
  )
}