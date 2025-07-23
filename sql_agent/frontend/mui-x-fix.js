// This script patches the MUI X Date Pickers modules to add .js extensions to imports
const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Function to add .js extension to import statements
function addJsExtension(content) {
  // Replace imports from @mui packages without extensions
  return content.replace(
    /from ['"](@mui\/[^/'"]+\/[^/'"]+)['"];/g, 
    'from "$1.js";'
  );
}

// Find all JS files in the node_modules/@mui/x-date-pickers directory
const muiFiles = glob.sync('node_modules/@mui/x-date-pickers/**/*.js');

console.log(`Found ${muiFiles.length} MUI X Date Pickers files to patch`);

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

console.log('MUI X Date Pickers patching complete!');