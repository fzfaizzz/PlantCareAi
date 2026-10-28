import sharp from 'sharp';
import Busboy from 'busboy';
import { ApiError } from './errors.mjs';

sharp.cache(false);
sharp.concurrency(1);

export function readMultipartImage(req, { maxFileBytes, maxRequestBytes, uploadTimeoutMs }, signal) {
  return new Promise((resolve, reject) => {
    const declared = req.headers['content-length'];
    if (declared && (!/^\d+$/.test(declared) || Number(declared) > maxRequestBytes)) {
      req.resume();
      reject(new ApiError(413, 'image_too_large', 'The upload exceeds the 4 MiB image limit.'));
      return;
    }
    if (!String(req.headers['content-type'] || '').toLowerCase().startsWith('multipart/form-data')) {
      req.resume();
      reject(new ApiError(415, 'multipart_required', "Send one image in multipart field 'image'."));
      return;
    }
    let parser;
    try {
      parser = Busboy({ headers: req.headers, limits: {
        files: 1, fields: 0, parts: 2, fileSize: maxFileBytes,
        fieldSize: 0, headerPairs: 30,
      } });
    } catch {
      req.resume();
      reject(new ApiError(400, 'invalid_multipart', 'The upload format is invalid.'));
      return;
    }
    let finished = false;
    let rawBytes = 0;
    let fileCount = 0;
    let chunks = [];
    let fileBytes = 0;
    const timer = setTimeout(() => fail(new ApiError(408, 'upload_timeout', 'The image upload timed out.')), uploadTimeoutMs);
    timer.unref?.();

    function cleanup() {
      clearTimeout(timer);
      req.off('data', trackBytes);
      req.off('aborted', aborted);
      req.off('error', streamError);
      signal?.removeEventListener('abort', aborted);
    }
    function fail(error) {
      if (finished) return;
      finished = true;
      cleanup();
      chunks = [];
      req.unpipe(parser);
      queueMicrotask(() => parser.destroy());
      req.resume();
      reject(error);
    }
    function trackBytes(chunk) {
      rawBytes += chunk.length;
      if (rawBytes > maxRequestBytes) fail(new ApiError(413, 'image_too_large', 'The multipart upload is too large.'));
    }
    function aborted() { fail(new ApiError(499, 'cancelled', 'The image request was cancelled.')); }
    function streamError() { fail(new ApiError(400, 'invalid_upload', 'The upload could not be read.')); }

    parser.on('file', (field, file) => {
      file.on('error', streamError);
      fileCount += 1;
      if (field !== 'image' || fileCount !== 1) {
        file.resume();
        fail(new ApiError(422, 'image_required', "Provide exactly one image in field 'image'."));
        return;
      }
      file.on('limit', () => fail(new ApiError(413, 'image_too_large', 'Images must be at most 4 MiB after optimization.')));
      file.on('error', streamError);
      file.on('data', chunk => {
        if (finished) return;
        fileBytes += chunk.length;
        if (fileBytes > maxFileBytes) {
          fail(new ApiError(413, 'image_too_large', 'Images must be at most 4 MiB after optimization.'));
          return;
        }
        chunks.push(chunk);
      });
    });
    parser.on('field', () => fail(new ApiError(422, 'image_required', 'Only one image field is accepted.')));
    parser.on('fieldsLimit', () => fail(new ApiError(422, 'image_required', 'Only one image field is accepted.')));
    parser.on('filesLimit', () => fail(new ApiError(422, 'image_required', 'Only one image per request is accepted.')));
    parser.on('partsLimit', () => fail(new ApiError(422, 'image_required', 'The multipart upload contains extra fields.')));
    parser.on('error', () => fail(new ApiError(400, 'invalid_multipart', 'The upload is incomplete or invalid.')));
    parser.on('close', () => {
      if (finished) return;
      if (fileCount !== 1 || fileBytes === 0) {
        fail(new ApiError(422, 'empty_image', 'Choose a non-empty JPEG, PNG, or WebP image.'));
        return;
      }
      finished = true;
      cleanup();
      const image = Buffer.concat(chunks, fileBytes);
      chunks = [];
      resolve(image);
    });
    req.on('data', trackBytes);
    req.once('aborted', aborted);
    req.once('error', streamError);
    signal?.addEventListener('abort', aborted, { once: true });
    if (signal?.aborted) return aborted();
    req.pipe(parser);
  });
}

function permittedMagic(data) {
  return (data.length >= 3 && data[0] === 0xff && data[1] === 0xd8 && data[2] === 0xff)
    || (data.length >= 8 && data.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])))
    || (data.length >= 12 && data.toString('ascii', 0, 4) === 'RIFF' && data.toString('ascii', 8, 12) === 'WEBP');
}

export async function normalizeImage(data, settings) {
  if (!data.length) throw new ApiError(422, 'empty_image', 'Choose a non-empty image.');
  if (!permittedMagic(data)) throw new ApiError(415, 'unsupported_image_format', 'Only actual JPEG, PNG, and WebP images are supported.');
  try {
    const options = { limitInputPixels: settings.maxImagePixels, sequentialRead: true, failOn: 'error', animated: true };
    const metadata = await sharp(data, options).metadata();
    if (!['jpeg', 'png', 'webp'].includes(metadata.format)) {
      throw new ApiError(415, 'unsupported_image_format', 'Only JPEG, PNG, and WebP images are supported.');
    }
    if ((metadata.pages || 1) !== 1) throw new ApiError(415, 'animated_image', 'Animated and multi-frame images are not supported.');
    if (Math.min(metadata.width || 0, metadata.height || 0) < 64) {
      throw new ApiError(422, 'poor_quality_image', 'Use a clear image at least 64 pixels wide and high.');
    }
    if (metadata.width * metadata.height > settings.maxImagePixels || Math.max(metadata.width, metadata.height) > 12000) {
      throw new ApiError(422, 'image_dimensions_exceeded', 'Resize this image before uploading.');
    }
    // Sharp removes metadata by default. Rotation applies EXIF orientation before removal.
    const jpeg = await sharp(data, options).rotate().resize({
      width: 1600, height: 1600, fit: 'inside', withoutEnlargement: true,
    }).flatten({ background: '#ffffff' }).toColourspace('srgb').jpeg({ quality: 85 }).toBuffer();
    const stats = await sharp(jpeg).resize(64, 64, { fit: 'fill' }).stats();
    const qualityWarnings = [];
    if (stats.channels.every(channel => channel.stdev < 4)) {
      qualityWarnings.push('The photo has very little visual detail; an in-focus close-up may work better.');
    }
    return { jpeg, width: metadata.width, height: metadata.height, qualityWarnings };
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (/pixel limit|exceeds.*limit/i.test(error.message || '')) {
      throw new ApiError(422, 'image_dimensions_exceeded', 'The decoded image is too large. Resize it first.');
    }
    throw new ApiError(422, 'invalid_image', 'The file is not a valid, complete JPEG, PNG, or WebP image.');
  }
}
