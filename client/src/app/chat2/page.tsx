"use client";

import { useEffect, useState } from 'react';

type Message = { role: string; content: string };

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);

  const fetchMessages = async () => {
    const response = await fetch('/messages', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
    const data = await response.json();
    setMessages(data);
  };

  const sendMessage = async () => {
    if (input.trim()) {
    const response = await fetch('/messages', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: input
          }),
        });
      setInput("");
      fetchMessages();
    }
  };

  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h2>Parallex REST Chat</h2>
      <div style={{ border: "1px solid #ccc", padding: 10, height: 300, overflowY: "scroll" }}>
        {messages.map((msg, i) => (
          <p key={i}><strong>{msg.role}:</strong> {msg.content}</p>
        ))}
      </div>
      <input
        style={{ width: "80%", padding: 8 }}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
      />
      <button onClick={sendMessage} style={{ padding: 8 }}>Invia</button>
    </div>
  );
}
