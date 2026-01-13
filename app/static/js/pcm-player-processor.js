/**
 * PCM Player Processor - Plays PCM audio data from the agent
 */
class PCMPlayerProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Float32Array(0);
    this.port.onmessage = this.handleMessage.bind(this);
  }

  handleMessage(event) {
    // Convert incoming Int16Array to Float32Array
    const int16Data = new Int16Array(event.data);
    const float32Data = new Float32Array(int16Data.length);

    for (let i = 0; i < int16Data.length; i++) {
      float32Data[i] = int16Data[i] / 32768.0;
    }

    // Append to buffer
    const newBuffer = new Float32Array(this.buffer.length + float32Data.length);
    newBuffer.set(this.buffer);
    newBuffer.set(float32Data, this.buffer.length);
    this.buffer = newBuffer;
  }

  process(inputs, outputs, parameters) {
    const output = outputs[0];
    const channel = output[0];

    if (this.buffer.length >= channel.length) {
      // Copy data to output
      channel.set(this.buffer.slice(0, channel.length));
      // Remove played data from buffer
      this.buffer = this.buffer.slice(channel.length);
    } else if (this.buffer.length > 0) {
      // Play remaining buffer and fill rest with silence
      channel.set(this.buffer);
      channel.fill(0, this.buffer.length);
      this.buffer = new Float32Array(0);
    } else {
      // No data, output silence
      channel.fill(0);
    }

    return true;
  }
}

registerProcessor("pcm-player-processor", PCMPlayerProcessor);
