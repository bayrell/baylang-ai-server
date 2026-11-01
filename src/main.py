from workers import WorkerEntrypoint

class Default(WorkerEntrypoint):
    def __init__(self, *args, **kwargs):
        WorkerEntrypoint.__init__(self, *args, **kwargs)
        self.app = create_cloudflare_app(self.env)
        
    async def fetch(self, request):
        import asgi
        return await asgi.fetch(self.app, request.js_object, self.env)