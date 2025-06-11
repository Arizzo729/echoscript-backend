// EchoScript.AI — Advanced Automation Service (NodeJS)
const { exec } = require("child_process");
const path = require("path");
const fs = require("fs/promises");

// Promisified exec
const execPromise = (cmd) =>
  new Promise((resolve, reject) => {
    exec(cmd, (error, stdout, stderr) => {
      if (error) {
        console.error("❌ Whisper CLI Error:", stderr || stdout);
        reject(new Error(stderr || stdout));
      } else {
        resolve(stdout);
      }
    });
  });

/**
 * Transcribe an audio file using Whisper CLI
 * @param {string} tmpPath - Absolute path to audio
 * @param {string} langCode - Language code (default: "auto")
 * @param {string} model - Whisper model name
 * @returns {Promise<string>} - Transcript content
 */
async function transcribeFile(tmpPath, langCode = "auto", model = "base") {
  const outputDir = path.resolve(__dirname, "../transcripts");
  const outputBase = path.parse(tmpPath).name;
  const transcriptPath = path.join(outputDir, `${outputBase}.txt`);

  try {
    // Ensure output directory exists
    await fs.mkdir(outputDir, { recursive: true });

    const command = `python -m whisper "${tmpPath}" --language ${langCode} --output_format txt --model ${model} --output_dir "${outputDir}"`;
    await execPromise(command);

    // Check for resulting transcript
    const transcript = await fs.readFile(transcriptPath, "utf-8");
    return transcript.trim();
  } catch (err) {
    console.error("❌ Transcription error:", err.message);
    throw new Error("Whisper transcription failed: " + err.message);
  }
}

module.exports = {
  transcribeFile,
};

