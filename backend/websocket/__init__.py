# WebSocket package
def __init__(self, db_session=None):

    self.db_session = db_session

    # LOAD STT MODEL ONLY ONCE
    if not hasattr(
        VoiceAgentWebSocketHandler,
        "_stt_service"
    ):
        print("[INIT] Loading STT model...")
        VoiceAgentWebSocketHandler._stt_service = (
            STTService()
        )

    # LOAD TTS ONLY ONCE
    if not hasattr(
        VoiceAgentWebSocketHandler,
        "_tts_service"
    ):
        print("[INIT] Loading TTS service...")
        VoiceAgentWebSocketHandler._tts_service = (
            TTSService()
        )

    self.stt_service = (
        VoiceAgentWebSocketHandler._stt_service
    )

    self.tts_service = (
        VoiceAgentWebSocketHandler._tts_service
    )

    self.language_detector = (
        LanguageDetectionService()
    )

    self.orchestrator = LLMService()

    self.redis_memory = (
        RedisMemoryManager()
    )

    self.persistent_memory = (
        PersistentMemoryManager(db_session)
        if db_session
        else None
    )