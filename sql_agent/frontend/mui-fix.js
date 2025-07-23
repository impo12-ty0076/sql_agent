// This script patches the MUI modules to add .js extensions to imports
const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Function to add .js extension to import statements
function addJsExtension(content) {
  // Replace imports from @mui packages without extensions
  // More comprehensive regex to catch different import patterns
  return content
    .replace(
      /from ['"](@mui\/[^/'"]+\/[^/'"]+)['"];/g, 
      'from "$1.js";'
    )
    .replace(
      /from ['"](@mui\/[^/'"]+\/esm\/[^/'"]+)['"];/g,
      'from "$1.js";'
    )
    .replace(
      /import\s+(?:(?:\* as )?[^*{},]+|\{[^{}]*\})\s+from\s+['"](@mui\/[^/'"]+\/[^.'"][^/'"]+)['"];/g,
      (match, p1) => match.replace(p1, `${p1}.js`)
    );
}

// Find all JS files in the node_modules/@mui directory
const muiFiles = glob.sync('node_modules/@mui/**/*.js');

console.log(`Found ${muiFiles.length} MUI files to patch`);

// Process each file
muiFiles.forEach(file => {
  try {
    const content = fs.readFileSync(file, 'utf8');
    const newContent = addJsExtension(content);
    
    // Only write if content changed
    if (content !== newContent) {
      fs.writeFileSync(file, newContent);
      console.log(`Patched: ${file}`);
    }
  } catch (error) {
    console.error(`Error processing ${file}:`, error);
  }
});

// Specifically check for the createSvgIcon issue
const systemFiles = glob.sync('node_modules/@mui/system/esm/**/*.js');
console.log(`Found ${systemFiles.length} MUI system files to check`);

systemFiles.forEach(file => {
  try {
    const content = fs.readFileSync(file, 'utf8');
    // Check if this file might be importing from material without extension
    if (content.includes('@mui/material') && !content.includes('@mui/material.js')) {
      const newContent = content.replace(
        /from ['"](@mui\/material\/[^/'"]+)['"];/g,
        'from "$1.js";'
      );
      if (content !== newContent) {
        fs.writeFileSync(file, newContent);
        console.log(`Fixed material imports in: ${file}`);
      }
    }
  } catch (error) {
    console.error(`Error processing ${file}:`, error);
  }
});

console.log('Patching complete!');