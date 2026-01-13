/**
 * PCM Recorder Processor - Records audio from microphone for voice input
 */
class PCMRecorderProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.bufferSize = 4800; // 200ms at 24kHz
    this.buffer = new Float32Array(this.bufferSize);
    this.bufferIndex = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];

    if (!input || !input[0]) {
      return true;
    }

    const channel = input[0];

    for (let i = 0; i < channel.length; i++) {
      this.buffer[this.bufferIndex++] = channel[i];

      if (this.bufferIndex >= this.bufferSize) {
        // Convert Float32Array to Int16Array for transmission
        const int16Data = new Int16Array(this.bufferSize);
        for (let j = 0; j < this.bufferSize; j++) {
          // Clamp value between -1 and 1
          const clamped = Math.max(-1, Math.min(1, this.buffer[j]));
          int16Data[j] = clamped < 0 ? clamped * 32768 : clamped * 32767;
        }

        // Send to main thread
        this.port.postMessage(int16Data.buffer);

        // Reset buffer
        this.bufferIndex = 0;
      }
    }

    return true;
  }
}

registerProcessor("pcm-recorder-processor", PCMRecorderProcessor);
