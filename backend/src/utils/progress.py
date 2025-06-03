class ProgressTracker:
    def __init__(self):
        self.handler = None
    
    def update_status(self, agent, ticker, status):
        if self.handler:
            self.handler.update_status(agent, ticker, status)
        else:
            # Default implementation - print to console
            if ticker:
                print(f"[{agent}] {ticker}: {status}")
            else:
                print(f"[{agent}] {status}")
    
    def start(self):
        if self.handler:
            self.handler.start()
    
    def complete(self):
        if self.handler:
            self.handler.complete()

# Global instance
progress = ProgressTracker() 