/**
 * Чат с ИИ-агентом: отправка сообщений и приём ответа со стримингом (SSE).
 */
import ChatPage from "./ChatPage.vue";
import BasePageModel from "@/pages/BasePageModel";
import { api } from "@/services/api";

export class ChatPageModel extends BasePageModel
{
    state = {
        params: {},
        chatId: null,
        title: "",
        agentName: "",
        messages: [],
        input: "",
        typing: false,
        streaming: false,
        loading: false,
        error: "",
    };

    getComponent()
    {
        return ChatPage;
    }

    getTitle()
    {
        return this.state.title || "Чат";
    }

    async init(params = {})
    {
        const chatId = Number(params.id || this.state.params.id);
        this.state.chatId = chatId;
        this.state.messages = [];
        this.state.error = "";

        if (!chatId) {
            this.state.error = "Чат не найден";
            return;
        }

        this.state.loading = true;

        try {
            const data = await api.get(`/api/chats/${chatId}`);
            this.state.title = data.chat.title || "Чат";
            this.state.agentName = data.chat.agent_name || "";
            this.state.messages = (data.messages || []).map(item => ({
                id: item.id,
                role: item.role,
                content: item.content,
                created_at: item.created_at,
            }));
        } catch (error) {
            this.state.error = error.message || "Не удалось загрузить чат";
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Отправить сообщение агенту (со стримингом ответа).
     */
    async send()
    {
        const content = (this.state.input || "").trim();
        if (!content || this.state.typing) {
            return;
        }

        this.state.input = "";
        this.state.typing = true;
        this.state.streaming = true;
        this.state.error = "";

        this.state.messages.push({ role: "user", content, id: null });
        const answer = { role: "assistant", content: "", id: null };
        this.state.messages.push(answer);

        try {
            await this.streamMessage(content, answer);
        } catch (error) {
            this.state.error = error.message || "Ошибка отправки сообщения";
            this.state.messages = this.state.messages.filter(item => item !== answer);
        } finally {
            this.state.typing = false;
            this.state.streaming = false;
        }
    }

    /**
     * Читать SSE-поток ответа агента.
     */
    async streamMessage(content, answer)
    {
        const token = localStorage.getItem("access_token");
        const response = await fetch(`/api/chats/${this.state.chatId}/stream`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(token ? { "Authorization": `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ content }),
        });

        if (!response.ok || !response.body) {
            let message = `Ошибка запроса (${response.status})`;
            try {
                const data = await response.json();
                if (data && data.detail) {
                    message = data.detail;
                }
            } catch (error) {
                /* не JSON */
            }
            throw new Error(message);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (!line.startsWith("data: ")) {
                    continue;
                }

                const payload = line.slice(6);
                if (payload === "[DONE]") {
                    continue;
                }

                let event;
                try {
                    event = JSON.parse(payload);
                } catch (error) {
                    continue;
                }

                if (event.type === "delta") {
                    answer.content += event.text || "";
                } else if (event.type === "done" && event.message) {
                    answer.id = event.message.id;
                } else if (event.type === "error") {
                    throw new Error(event.message || "Ошибка агента");
                }
            }
        }
    }

    /**
     * Добавить сообщение в поле ввода по Enter (Shift+Enter — перенос строки).
     */
    onKeydown(event)
    {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            this.send();
        }
    }

    /**
     * Очистить чат (создать новый).
     */
    async newChat()
    {
        try {
            const chat = await api.post("/api/chats", { title: "Новый чат" });
            await this.$layout.getRouter().open("chat", { id: chat.id });
        } catch (error) {
            this.state.error = error.message || "Не удалось создать чат";
        }
    }
}
