const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('Cleaning node_modules and reinstalling dependencies...');

try {
  // Remove node_modules
  console.log('Removing node_modules...');
  if (fs.existsSync('node_modules')) {
    execSync('rmdir /s /q node_modules', { stdio: 'inherit' });
  }

  // Remove package-lock.json
  console.log('Removing package-lock.json...');
  if (fs.existsSync('package-lock.json')) {
    fs.unlinkSync('package-lock.json');
  }

  // Clean npm cache
  console.log('Cleaning npm cache...');
  execSync('npm cache clean --force', { stdio: 'inherit' });

  // Reinstall dependencies
  console.log('Reinstalling dependencies...');
  execSync('npm install', { stdio: 'inherit' });

  console.log('Clean reinstall completed successfully!');
} catch (error) {
  console.error('Error during clean reinstall:', error);
  process.exit(1);
}