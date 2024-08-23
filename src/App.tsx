import cx from "./App.module.css";
import { useState } from "react";
import { useStateWithAsyncCallback } from "./useStateWithCallback";

import ScrollToBottom from "react-scroll-to-bottom";

import { ai } from "./useAi";

interface Conversation {
  role: 'user' | 'assistant',
  content: string,
  flags?: 'loading'
}

interface ConversationPayload {
  role: 'user' | 'assistant',
  content: string,
}

function UserMessage({ content }: { content: string }) {
  return (
    <div>
      <p className={cx.userMessage}>{content}</p>
    </div>
  )
}

function AIMessage({ content, loading }: { content: string, loading?: boolean }) {
  return (
    <div>
      <p className={cx.aiMessage} data-loading={loading}>{content}</p>
    </div>
  )
}

export default function App() {
  const [landing, setLanding] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);

  const [conversation, setConversation] = useStateWithAsyncCallback<Conversation[]>([]);
  const [convPayload, setConvPayload] = useStateWithAsyncCallback<ConversationPayload[]>([]);

  const [input, setInput] = useState<string>("");

  return (
    <div className={cx.wrapper}>
      {
        !landing && (
          <div className={cx.messagesWrapper}>
            <ScrollToBottom className={cx.messages}>
              {
                conversation.map(({ role, content, flags }, idx) => (
                  role == "user"
                    ? (
                      <UserMessage content={content} key={idx} />
                    )
                    : (
                      <AIMessage content={content} key={idx} loading={flags == 'loading'} />
                    )
                ))
              }
            </ScrollToBottom>
          </div>
        )
      }

      <div>
        <h1
          className={cx.title}
          style={{
            filter: landing ? "" : "blur(10px)",
            WebkitFilter: landing ? "" : "blur(10px)",
            opacity: landing ? 1 : 0,
            pointerEvents: landing ? "all" : "none"
          }}
        >
          What would you like to ask Maoyue?
        </h1>
        <div>
          <form
            onSubmit={e => {
              e.preventDefault();
              if (loading)
                return;

              setLanding(false);
              setConversation(conv => [...conv, { role: "user", content: input }])
              setInput("");

              setLoading(true);
              setTimeout(() => {
                async function runner() {
                  let mConv: Conversation[] = [...conversation, { role: "user", content: input }];
                  let mConvPayload: ConversationPayload[] = [...convPayload, { role: "user", content: input }];

                  for await (const result of ai(mConvPayload)) {
                    console.log(result);

                    if (mConv.length > 0 && mConv[mConv.length - 1].role == "assistant" && mConv[mConv.length - 1].flags == 'loading') {
                      mConv = await setConversation(mConv.slice(0, -1));
                    }

                    if (!result.background)
                      mConv = await setConversation(
                        [
                          ...mConv,
                          { role: "assistant", content: result['content'], flags: result['done'] ? undefined : 'loading' }
                        ]
                      );

                    mConvPayload = await setConvPayload(
                      [
                        ...mConvPayload,
                        { role: result.background ? "user" : "assistant", content: result['content'] }
                      ]
                    )
                  }
                  setLoading(false)
                }
                runner();
              }, 1000)
            }}
          >
            <input
              type="text"
              placeholder="Start typing..."
              className={cx.input}
              style={{
                transform: landing ? "" : "translateY(20rem)",
                height: landing ? "" : "60px",
                fontSize: landing ? "" : "20px"
              }}
              onChange={(e) => setInput(e.currentTarget.value)}
              value={input}
              autoFocus
            />
          </form>
        </div>
      </div>
    </div>
  )
}