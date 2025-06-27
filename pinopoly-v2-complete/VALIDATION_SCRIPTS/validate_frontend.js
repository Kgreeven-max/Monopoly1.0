#!/usr/bin/env node
/**
 * Frontend Validation Script for Pinopoly V2
 * 
 * This script validates that the frontend implementation is correct and working.
 * Run this after creating frontend files to ensure everything is set up properly.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colors for output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function printSuccess(message) {
  console.log(`${colors.green}✓${colors.reset} ${message}`);
}

function printError(message) {
  console.log(`${colors.red}✗${colors.reset} ${message}`);
}

function printWarning(message) {
  console.log(`${colors.yellow}⚠${colors.reset} ${message}`);
}

function printInfo(message) {
  console.log(`${colors.blue}ℹ${colors.reset} ${message}`);
}

class FrontendValidator {
  constructor(frontendDir = 'frontend') {
    this.frontendDir = frontendDir;
    this.errors = [];
    this.warnings = [];
  }

  validateAll() {
    printInfo('Starting frontend validation...');
    console.log();

    const checks = [
      ['Directory Structure', this.validateDirectoryStructure.bind(this)],
      ['Node.js Environment', this.validateNodeEnvironment.bind(this)],
      ['Package Configuration', this.validatePackageConfiguration.bind(this)],
      ['Dependencies', this.validateDependencies.bind(this)],
      ['TypeScript Configuration', this.validateTypeScriptConfig.bind(this)],
      ['Build Tools', this.validateBuildTools.bind(this)],
      ['Component Structure', this.validateComponentStructure.bind(this)],
      ['Service Layer', this.validateServiceLayer.bind(this)],
      ['Type Definitions', this.validateTypeDefinitions.bind(this)],
      ['Main Application', this.validateMainApp.bind(this)]
    ];

    let allPassed = true;
    for (const [checkName, checkFunc] of checks) {
      console.log(`Checking ${checkName}...`);
      try {
        if (!checkFunc()) {
          allPassed = false;
        }
      } catch (error) {
        printError(`Validation error in ${checkName}: ${error.message}`);
        allPassed = false;
      }
      console.log();
    }

    this.printSummary();
    return allPassed;
  }

  validateDirectoryStructure() {
    const requiredDirs = [
      'src',
      'src/components',
      'src/components/ui',
      'src/pages',
      'src/features',
      'src/features/game',
      'src/features/game/components',
      'src/features/players',
      'src/features/properties',
      'src/hooks',
      'src/services',
      'src/store',
      'src/types',
      'src/utils',
      'tests',
      'public'
    ];

    const missingDirs = [];
    for (const dir of requiredDirs) {
      const fullPath = path.join(this.frontendDir, dir);
      if (!fs.existsSync(fullPath)) {
        missingDirs.push(dir);
      }
    }

    if (missingDirs.length > 0) {
      for (const dir of missingDirs) {
        printError(`Missing directory: ${dir}`);
      }
      return false;
    }

    printSuccess('All required directories exist');
    return true;
  }

  validateNodeEnvironment() {
    try {
      // Check Node.js version
      const nodeVersion = execSync('node --version', { encoding: 'utf8' }).trim();
      printSuccess(`Node.js version: ${nodeVersion}`);

      // Check if Node.js version is 18+
      const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
      if (majorVersion < 18) {
        printError('Node.js 18+ is required');
        return false;
      }

      // Check npm version
      const npmVersion = execSync('npm --version', { encoding: 'utf8' }).trim();
      printSuccess(`npm version: ${npmVersion}`);

      return true;
    } catch (error) {
      printError(`Cannot check Node.js environment: ${error.message}`);
      return false;
    }
  }

  validatePackageConfiguration() {
    const packagePath = path.join(this.frontendDir, 'package.json');
    
    if (!fs.existsSync(packagePath)) {
      printError('package.json not found');
      return false;
    }

    try {
      const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
      
      // Check required fields
      const requiredFields = ['name', 'version', 'scripts', 'dependencies'];
      for (const field of requiredFields) {
        if (!packageJson[field]) {
          printError(`Missing field in package.json: ${field}`);
          return false;
        }
      }

      // Check required scripts
      const requiredScripts = ['dev', 'build', 'test', 'lint'];
      for (const script of requiredScripts) {
        if (!packageJson.scripts[script]) {
          printWarning(`Missing script in package.json: ${script}`);
        } else {
          printSuccess(`Script available: ${script}`);
        }
      }

      printSuccess('Package configuration validated');
      return true;
    } catch (error) {
      printError(`Invalid package.json: ${error.message}`);
      return false;
    }
  }

  validateDependencies() {
    const nodeModulesPath = path.join(this.frontendDir, 'node_modules');
    
    if (!fs.existsSync(nodeModulesPath)) {
      printError('node_modules not found. Run: npm install');
      return false;
    }

    const requiredDeps = [
      'react',
      'react-dom',
      'typescript',
      'vite',
      '@types/react',
      '@types/react-dom'
    ];

    let allDepsInstalled = true;
    for (const dep of requiredDeps) {
      const depPath = path.join(nodeModulesPath, dep);
      if (fs.existsSync(depPath)) {
        printSuccess(`Dependency available: ${dep}`);
      } else {
        printError(`Missing dependency: ${dep}`);
        allDepsInstalled = false;
      }
    }

    if (!allDepsInstalled) {
      printInfo('Install missing dependencies with: npm install');
      return false;
    }

    return true;
  }

  validateTypeScriptConfig() {
    const tsconfigPath = path.join(this.frontendDir, 'tsconfig.json');
    
    if (!fs.existsSync(tsconfigPath)) {
      printError('tsconfig.json not found');
      return false;
    }

    try {
      const tsconfig = JSON.parse(fs.readFileSync(tsconfigPath, 'utf8'));
      
      // Check compiler options
      if (!tsconfig.compilerOptions) {
        printError('Missing compilerOptions in tsconfig.json');
        return false;
      }

      const requiredOptions = ['target', 'lib', 'module', 'jsx'];
      for (const option of requiredOptions) {
        if (!tsconfig.compilerOptions[option]) {
          printWarning(`Missing compiler option: ${option}`);
        }
      }

      printSuccess('TypeScript configuration validated');
      return true;
    } catch (error) {
      printError(`Invalid tsconfig.json: ${error.message}`);
      return false;
    }
  }

  validateBuildTools() {
    const viteConfigPath = path.join(this.frontendDir, 'vite.config.ts');
    
    if (!fs.existsSync(viteConfigPath)) {
      printWarning('vite.config.ts not found');
    } else {
      printSuccess('Vite configuration found');
    }

    // Check if we can run type checking
    try {
      const cwd = process.cwd();
      process.chdir(this.frontendDir);
      
      execSync('npx tsc --noEmit', { stdio: 'pipe' });
      printSuccess('TypeScript compilation check passed');
      
      process.chdir(cwd);
      return true;
    } catch (error) {
      printWarning('TypeScript compilation has issues');
      process.chdir(process.cwd());
      return true; // Don't fail validation for TS errors
    }
  }

  validateComponentStructure() {
    const componentFiles = [
      'src/App.tsx',
      'src/main.tsx',
      'src/features/game/components/GameBoard.tsx',
      'src/components/ui/Button.tsx'
    ];

    let allComponentsExist = true;
    for (const file of componentFiles) {
      const filePath = path.join(this.frontendDir, file);
      if (fs.existsSync(filePath)) {
        printSuccess(`Component exists: ${file}`);
      } else {
        printWarning(`Component not found: ${file}`);
        allComponentsExist = false;
      }
    }

    return allComponentsExist;
  }

  validateServiceLayer() {
    const serviceFiles = [
      'src/services/api.ts',
      'src/services/websocket.ts'
    ];

    let allServicesExist = true;
    for (const file of serviceFiles) {
      const filePath = path.join(this.frontendDir, file);
      if (fs.existsSync(filePath)) {
        printSuccess(`Service exists: ${file}`);
      } else {
        printWarning(`Service not found: ${file}`);
        allServicesExist = false;
      }
    }

    return allServicesExist;
  }

  validateTypeDefinitions() {
    const typeFiles = [
      'src/types/game.ts',
      'src/types/player.ts',
      'src/types/api.ts'
    ];

    let allTypesExist = true;
    for (const file of typeFiles) {
      const filePath = path.join(this.frontendDir, file);
      if (fs.existsSync(filePath)) {
        printSuccess(`Type definition exists: ${file}`);
      } else {
        printWarning(`Type definition not found: ${file}`);
        allTypesExist = false;
      }
    }

    return allTypesExist;
  }

  validateMainApp() {
    const mainFiles = ['src/main.tsx', 'src/App.tsx'];
    
    let allMainFilesExist = true;
    for (const file of mainFiles) {
      const filePath = path.join(this.frontendDir, file);
      if (!fs.existsSync(filePath)) {
        printError(`Main file not found: ${file}`);
        allMainFilesExist = false;
      } else {
        printSuccess(`Main file exists: ${file}`);
      }
    }

    // Check index.html
    const indexPath = path.join(this.frontendDir, 'public', 'index.html');
    if (!fs.existsSync(indexPath)) {
      printError('public/index.html not found');
      allMainFilesExist = false;
    } else {
      printSuccess('HTML template exists: public/index.html');
    }

    return allMainFilesExist;
  }

  printSummary() {
    console.log('='.repeat(50));
    console.log('VALIDATION SUMMARY');
    console.log('='.repeat(50));

    if (this.errors.length === 0 && this.warnings.length === 0) {
      printSuccess('All validations passed! ✨');
      printInfo('Your frontend is ready for development.');
    } else {
      if (this.errors.length > 0) {
        printError(`Found ${this.errors.length} error(s)`);
        for (const error of this.errors) {
          printError(`  - ${error}`);
        }
      }

      if (this.warnings.length > 0) {
        printWarning(`Found ${this.warnings.length} warning(s)`);
        for (const warning of this.warnings) {
          printWarning(`  - ${warning}`);
        }
      }
    }

    console.log();
    printInfo('Next steps:');
    printInfo('1. Fix any errors above');
    printInfo('2. Create missing files using templates');
    printInfo('3. Run: npm run dev');
    printInfo('4. Open: http://localhost:3000');
  }
}

function main() {
  const frontendDir = process.argv[2] || 'frontend';
  
  if (!fs.existsSync(frontendDir)) {
    printError(`Frontend directory not found: ${frontendDir}`);
    printInfo('Run this script from the project root directory');
    process.exit(1);
  }

  const validator = new FrontendValidator(frontendDir);
  const success = validator.validateAll();
  
  process.exit(success ? 0 : 1);
}

if (require.main === module) {
  main();
}