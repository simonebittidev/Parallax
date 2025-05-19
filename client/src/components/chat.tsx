'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import clsx from 'clsx';
import { onAuthStateChanged, User } from 'firebase/auth'
import { logOut, auth } from '../lib/firebase'
import { PlusIcon } from '@heroicons/react/24/solid';
import { useRouter } from 'next/navigation';

const TypewriterText = ({ text }: { text: string }) => {
  const [displayedText, setDisplayedText] = useState('');
  const indexRef = useRef(0);

  useEffect(() => {
    indexRef.current = 0;
    setDisplayedText('');

    const type = () => {
      setDisplayedText(prev => {
        const nextChar = text.charAt(indexRef.current);
        indexRef.current += 1;
        return prev + nextChar;
      });

      if (indexRef.current < text.length) {
        setTimeout(type, 15);
      }
    };

    const timeout = setTimeout(type, 300); // ritardo iniziale di 300ms
    return () => clearTimeout(timeout);
  }, [text]);

  return <span>{displayedText}</span>;
};

type ChatMessage = {
  role: 'human' | 'ai';
  agent_name: 'Opposite' | 'Neutral' | 'Emphatic' | "";
  content: string;
};

const ChatContent = () => {
  const params = useSearchParams();
  const chatBoxRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const perspective = params.get('perspective') as ChatMessage['agent_name'] | null;
  const conv_id = params.get('conv_id') as string || null;
  const [activePerspectives, setActivePerspectives] = useState<string[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [suggestionsVisible, setSuggestionsVisible] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState<string[]>([]);

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
        router.push("/home");
      }
  
      const messages = JSON.parse(await response.json());
      console.log('Messaggi ricevuti:', messages);

      if (Array.isArray(messages)) {
        console.log('messaggi ricevuti in formato array');
        setChatMessages(messages);
      }

    } catch (error) {
      console.error('Errore durante la chiamata al server:', error);
      // alert('Si è verificato un errore durante la comunicazione con il server.');
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

    if (!userId || !conv_id) {
      console.error('User ID or conversation ID is not available.');
      return;
    }
    
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";

    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/${userId}/${conv_id}`);
    
    console.log(`WebSocket URL: ${protocol}://${window.location.host}/ws/${userId}/${conv_id}`);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log("✅ WebSocket connesso");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (typeof data === "object" && data !== null && "event" in data) {
          const typingMsg = `${data["agent_name"]} is typing...`;
          setIsTyping(prev => (prev.includes(typingMsg) ? prev : [...prev, typingMsg]));

          // Timeout automatico per rimuovere dopo 3s
          setTimeout(() => {
            setIsTyping(prev => prev.filter(item => item !== typingMsg));
          }, 3000);
        }
        else{
          const messages = JSON.parse(data);
          if (Array.isArray(messages)) {
            const lastElement = messages[messages.length - 1];

            setIsTyping(prev => prev.filter(item => item !== `${lastElement.agent_name} is typing...`));

            console.log(JSON.stringify(messages));
            console.log('messaggi ws ricevuti in formato array');
            setChatMessages(messages);
          }else{
            console.log('messaggi ws non ricevuti in formato array');
            console.log(messages);
          }
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

    let agent = null;
    let contentToSend = chatInput.trim();

    const match = contentToSend.match(/^@(\w+)\s+(.*)/);
    if (match) {
      const tag = match[1].toLowerCase();
      if (['opposite', 'neutral', 'emphatic'].includes(tag)) {
        agent = tag.charAt(0).toUpperCase() + tag.slice(1);
        contentToSend = match[2];
      }
    }

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ text: contentToSend, target_agent: agent }));
      setChatInput("");
      setChatMessages([...chatMessages, { role: 'human', agent_name: '', content: contentToSend }]);
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


const MOBILE_WIDTH = 768;

  const [isInputFocused, setInputFocused] = useState(false);
  // Per evitare errori SSR/Next.js: controlliamo che sia client-side
  const isMobile =
    typeof window !== "undefined" && window.innerWidth < MOBILE_WIDTH;

  return (
    <div className="flex flex-col h-screen items-center justify-center">
      <div className="flex flex-col h-full w-full max-w-xl mx-auto">
      <div className="h-16 w-full mt-20">
        <div className="flex-1 overflow-y-auto p-4" ref={chatBoxRef} style={{
          paddingBottom: isInputFocused && isMobile ? "270px" : "150px",
          transition: "padding-bottom 0.2s",
        }}>
          {chatMessages.map((msg, i) => (
            <div key={i} className={`mb-5 flex items-start gap-2 ${msg.role === 'human' ? 'justify-end' : 'justify-start'}`}>
              {msg.role !== 'human' && (
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
                className={`rounded-xl px-5 py-3 text-sm max-w-[80%] whitespace-pre-line ${msg.role === 'human' ? 'bg-black text-white' : 'bg-gray-100 text-black'}`}
              >
                {/* {msg.role === 'user' ? msg.content : <TypewriterText text={msg.content} />} */}
                {msg.content}
              </div>

              

            </div>
          ))}

          {isTyping.map((typing, i) => (
            <div className="text-gray-500 text-sm px-10">
              {typing}
            </div>
          ))}
        </div>

        
      </div>
      <div className="p-4 bg-white fixed bottom-0 left-0 right-0 z-20 w-full flex justify-center">
        <div className="w-full max-w-xl">
      {['Opposite', 'Neutral', 'Emphatic']
        .filter(p => !chatMessages.some(msg => msg.agent_name === p) && !activePerspectives.includes(p))
        .map(p => (
          <button
            key={p}
            onKeyDown={(e) => e.key === 'Enter' && handle_new_pov(p)}
            onClick={() => {
              setActivePerspectives(prev => [...prev, p]); // nasconde subito il pulsante
              handle_new_pov(p);
            }}
            className="mt-2 inline-flex items-center px-6 py-2 bg-gray-100 rounded-full border border-gray-300 hover:bg-gray-200 transition mr-2"
          >
            <PlusIcon className="size-5 mr-2" /> {p}
          </button>
      ))}
    

    <div tabIndex={0}  className=" mt-2 flex gap-2 border p-2 rounded-2xl border-gray-300 bg-gray-100 h-20 focus-within:ring-2 focus-within:ring-indigo-600 focus-within:outline-none">
      <textarea
        ref={inputRef}
        value={chatInput}
        onChange={(e) => {
          const value = e.target.value;
          setChatInput(value);
          if (value.endsWith('@')) {
            setFilteredSuggestions(['Opposite', 'Neutral', 'Emphatic']);
            setSuggestionsVisible(true);
          } else {
            setSuggestionsVisible(false);
          }
        }}
        placeholder="Write your message..."
        onKeyDown={(e) => { if (e.key === 'Enter'){e.preventDefault(); handleSend();}}}
        className="flex-1 hover:bg-gray-100 focus:outline-none"
        onFocus={() => {
          setInputFocused(true);
          inputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
        }}
        onBlur={() => {
          setInputFocused(false);
          setTimeout(() => {
            inputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
          }, 100);
        }}
      />
      {suggestionsVisible && (
        <div className="absolute mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-10 p-2">
          {filteredSuggestions.map((s) => (
            <div
              key={s}
              className="cursor-pointer px-2 py-1 hover:bg-indigo-100"
              onClick={() => {
                setChatInput(chatInput + s + ' ');
                setSuggestionsVisible(false);
              }}
            >
              @{s}
            </div>
          ))}
        </div>
      )}
      <button
        onClick={handleSend}
        className="bottom-3 right-3 w-10 h-10 bg-indigo-600 text-white rounded-full flex items-center justify-center hover:bg-indigo-600-dark"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="w-5 h-5">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
        </svg>
      </button>
    </div>
    </div>
    </div>
    </div>
    </div>
  );
};

export default ChatContent;