import { useState } from "react";

import { Badge } from "../../components/common/Badge.jsx";

export function ChatPanel({ ticker, messages, onSend }) {
  const [input, setInput] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text) {
      return;
    }
    setInput("");
    await onSend(text);
  }

  return (
    <section className="panel wide chat-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Local analyst</p>
          <h2>{ticker} Analyst Chat</h2>
        </div>
        <Badge value="local sqlite" />
      </div>

      <div className="chat-log">
        {messages.map((message, index) => (
          <div className={`chat-message ${message.role}`} key={index}>
            {message.text}
          </div>
        ))}
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={`Ask about ${ticker}, sentiment, cache, crypto, FX, or provider health...`}
        />
        <button type="submit">Send</button>
      </form>
    </section>
  );
}
