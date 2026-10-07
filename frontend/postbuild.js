import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const assetsDir = path.join(__dirname, 'dist', 'assets');

if (fs.existsSync(assetsDir)) {
  const files = fs.readdirSync(assetsDir);
  const jsFiles = files.filter(f => f.endsWith('.js') && f.startsWith('index-'));
  const cssFiles = files.filter(f => f.endsWith('.css') && f.startsWith('index-'));

  if (jsFiles.length > 0) {
    // Pick the most recent generated bundle
    const mainJs = jsFiles[0];
    const mainJsPath = path.join(assetsDir, mainJs);

    // List of known previous hashes that browsers might have cached
    const aliases = [
      'index-B5y521HA.js',
      'index-Dy3Nsx9z.js',
      'index-kDqYTRGs.js',
      'index-CnOJ5Hr-.js',
      'index-D9WQbgAR.js',
      'index-latest.js'
    ];

    aliases.forEach(alias => {
      const aliasPath = path.join(assetsDir, alias);
      try {
        fs.copyFileSync(mainJsPath, aliasPath);
        console.log(`[postbuild] Created asset alias: ${alias} -> ${mainJs}`);
      } catch (err) {
        console.error(`[postbuild] Failed to create alias ${alias}:`, err);
      }
    });
  }

  if (cssFiles.length > 0) {
    const mainCss = cssFiles[0];
    const mainCssPath = path.join(assetsDir, mainCss);
    const cssAliases = [
      'index-CuPQKCmo.css',
      'index-DCvwHi_m.css',
      'index-latest.css'
    ];
    cssAliases.forEach(alias => {
      const aliasPath = path.join(assetsDir, alias);
      try {
        fs.copyFileSync(mainCssPath, aliasPath);
        console.log(`[postbuild] Created CSS alias: ${alias} -> ${mainCss}`);
      } catch (err) {
        console.error(`[postbuild] Failed to create CSS alias ${alias}:`, err);
      }
    });
  }
}
