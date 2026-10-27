"""
Módulo de captura de audio y reconocimiento de voz offline continuo mediante Vosk y sounddevice.
Ejecuta la escucha en un hilo independiente (QThread) para mantener la GUI 100% fluida.
"""
import json
import queue
import sounddevice as sd
from PySide6.QtCore import QThread, Signal
import vosk


class VoiceListenerWorker(QThread):
    """
    Hilo de ejecución en segundo plano para captura de audio y transcripción continua offline.
    """
    command_detected = Signal(str)        # Transcripción final de la frase dictada
    partial_detected = Signal(str)        # Transcripción parcial en tiempo real
    listening_state_changed = Signal(bool) # Notifica si la escucha está activa o inactiva
    status_message = Signal(str)          # Notificaciones de estado / errores

    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self._audio_queue = queue.Queue()
        self._model = None
        self._recognizer = None

    def initialize_model(self) -> bool:
        """Inicializa o carga el modelo de lenguaje en español."""
        if self._model is not None:
            return True
        try:
            self.status_message.emit("Cargando modelo de voz offline (español)...")
            # Carga el modelo local descargado en caché
            self._model = vosk.Model(lang="es")
            self._recognizer = vosk.KaldiRecognizer(self._model, self.SAMPLE_RATE)
            self._recognizer.SetWords(False)
            self.status_message.emit("Modelo de voz listo.")
            return True
        except Exception as e:
            self.status_message.emit(f"Error al inicializar modelo de voz: {str(e)}")
            return False

    def start_listening(self):
        """Inicia el proceso de escucha continua."""
        if not self._is_running:
            self._is_running = True
            self.start()

    def stop_listening(self):
        """Detiene de forma segura el hilo de escucha."""
        self._is_running = False
        self.wait(1500)
        self.listening_state_changed.emit(False)
        self.status_message.emit("Escucha de voz desactivada.")

    def is_listening(self) -> bool:
        return self._is_running

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback invocado por sounddevice con nuevos bloques de audio PCM."""
        if status:
            pass
        if self._is_running:
            self._audio_queue.put(bytes(indata))

    def run(self):
        """Bucle principal de procesamiento de audio en tiempo real."""
        if not self.initialize_model():
            self._is_running = False
            self.listening_state_changed.emit(False)
            return

        self.listening_state_changed.emit(True)
        self.status_message.emit("Escucha continua activa. Hable normalmente...")

        try:
            with sd.RawInputStream(
                samplerate=self.SAMPLE_RATE,
                blocksize=4000,
                dtype="int16",
                channels=self.CHANNELS,
                callback=self._audio_callback
            ):
                while self._is_running:
                    try:
                        # Extraer chunk con timeout breve para permitir parada limpia
                        data = self._audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    if self._recognizer.AcceptWaveform(data):
                        res_json = json.loads(self._recognizer.Result())
                        text = res_json.get("text", "").strip()
                        if text:
                            self.command_detected.emit(text)
                            self.partial_detected.emit("")
                    else:
                        partial_json = json.loads(self._recognizer.PartialResult())
                        partial = partial_json.get("partial", "").strip()
                        if partial:
                            self.partial_detected.emit(partial)

        except Exception as e:
            self.status_message.emit(f"Error en micrófono: {str(e)}")
        finally:
            self._is_running = False
            self.listening_state_changed.emit(False)
