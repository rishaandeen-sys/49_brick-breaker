import math
import struct
import pygame


class SoundManager:
    """Generates simple beep/chime sound effects at runtime so the
    game doesn't depend on any external audio asset files."""

    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.quit()
        except pygame.error:
            pass
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
        except pygame.error:
            self.enabled = False
            return

        self.sounds = {
            "wall": self._tone(220, 60),
            "paddle": self._tone(440, 70),
            "brick": self._chirp(700, 900, 90),
            "win": self._chime([523, 659, 784], 120),
            "lose": self._chime([400, 300, 200], 150),
        }

    def _tone(self, frequency, duration_ms, volume=0.25, sample_rate=44100):
        n_samples = int(sample_rate * duration_ms / 1000)
        buf = bytearray()
        amplitude = int(32767 * volume)
        for i in range(n_samples):
            t = i / sample_rate
            value = int(amplitude * math.sin(2 * math.pi * frequency * t))
            buf += struct.pack("<h", value)
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _chirp(self, f_start, f_end, duration_ms, volume=0.25, sample_rate=44100):
        n_samples = int(sample_rate * duration_ms / 1000)
        buf = bytearray()
        amplitude = int(32767 * volume)
        for i in range(n_samples):
            t = i / sample_rate
            freq = f_start + (f_end - f_start) * (i / n_samples)
            value = int(amplitude * math.sin(2 * math.pi * freq * t))
            buf += struct.pack("<h", value)
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _chime(self, frequencies, note_ms, volume=0.3, sample_rate=44100):
        buf = bytearray()
        amplitude = int(32767 * volume)
        for freq in frequencies:
            n_samples = int(sample_rate * note_ms / 1000)
            for i in range(n_samples):
                t = i / sample_rate
                value = int(amplitude * math.sin(2 * math.pi * freq * t))
                buf += struct.pack("<h", value)
        return pygame.mixer.Sound(buffer=bytes(buf))

    def play(self, name):
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.play()