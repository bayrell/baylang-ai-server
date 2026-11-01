/**
 * Стартовая страница: редирект на чаты или на форму входа.
 */
import IndexPage from "./IndexPage.vue";
import BasePageModel from "@/pages/BasePageModel";

export class IndexPageModel extends BasePageModel
{
    state = {
        params: {},
        redirecting: true,
    };

    getComponent()
    {
        return IndexPage;
    }

    getTitle()
    {
        return "BayLang AI";
    }

    async init()
    {
        const authenticated = Boolean(localStorage.getItem("access_token"));
        await this.$layout.getRouter().open(authenticated ? "chats" : "login", {}, { replace: true });
    }
}

export default IndexPageModel;
