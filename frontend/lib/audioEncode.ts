/**
 * Encode recorded audio as 16-bit PCM WAV for reliable Whisper transcription.
 */

function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

function floatTo16BitPCM(
  output: DataView,
  offset: number,
  input: Float32Array
) {
  for (let i = 0; i < input.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, input[i]));
    output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
}

function interleave(
  left: Float32Array,
  right: Float32Array
): Float32Array {
  const length = left.length + right.length;
  const result = new Float32Array(length);

  let index = 0;

  for (let i = 0; i < left.length; i++) {
    result[index++] = left[i];
    result[index++] = right[i];
  }

  return result;
}

export function encodeWavFromAudioBuffer(
  audioBuffer: AudioBuffer
): ArrayBuffer {
  const numChannels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;

  const samples =
    numChannels === 2
      ? interleave(
          audioBuffer.getChannelData(0),
          audioBuffer.getChannelData(1)
        )
      : audioBuffer.getChannelData(0);

  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numChannels * 2, true);
  view.setUint16(32, numChannels * 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, "data");
  view.setUint32(40, samples.length * 2, true);

  floatTo16BitPCM(view, 44, samples);

  return buffer;
}

export async function blobToWavArrayBuffer(
  blob: Blob
): Promise<ArrayBuffer> {
  if (typeof window === "undefined") {
    throw new Error("Browser only");
  }

  const arrayBuffer = await blob.arrayBuffer();

  const audioContext = new window.AudioContext();

  try {
    const decoded = await audioContext.decodeAudioData(
      arrayBuffer.slice(0)
    );

    return encodeWavFromAudioBuffer(decoded);
  } finally {
    await audioContext.close().catch(() => undefined);
  }
}

export function sniffAudioFormat(
  bytes: Uint8Array
): "wav" | "webm" | "mp4" | "unknown" {
  if (
    bytes.length >= 4 &&
    bytes[0] === 0x52 &&
    bytes[1] === 0x49 &&
    bytes[2] === 0x46 &&
    bytes[3] === 0x46
  ) {
    return "wav";
  }

  if (
    bytes.length >= 4 &&
    bytes[0] === 0x1a &&
    bytes[1] === 0x45 &&
    bytes[2] === 0xdf &&
    bytes[3] === 0xa3
  ) {
    return "webm";
  }

  if (
    bytes.length >= 8 &&
    bytes[4] === 0x66 &&
    bytes[5] === 0x74 &&
    bytes[6] === 0x79 &&
    bytes[7] === 0x70
  ) {
    return "mp4";
  }

  return "unknown";
}