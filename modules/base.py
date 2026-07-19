class BaseModule:
    def __init__(self, session, config, proxy_manager):
        self.session = session
        self.config = config
        self.proxy_manager = proxy_manager
        
    async def scan(self, target):
        raise NotImplementedError("Each module must implement scan()")
        
    def _get_proxy(self):
        return self.proxy_manager.get_proxy()
