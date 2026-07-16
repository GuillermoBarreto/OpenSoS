import fs from 'fs'
import path from 'path'

const projectsDir = path.resolve('daily-projects')
const today = new Date().toISOString().slice(0, 10)
const projectName = `project-${today}`
const projectPath = path.join(projectsDir, projectName)

if (!fs.existsSync(projectsDir)) {
  fs.mkdirSync(projectsDir)
}

if (fs.existsSync(projectPath)) {
  console.log(`A project already exists for today: ${projectName}`)
  process.exit(0)
}

fs.mkdirSync(projectPath)
fs.writeFileSync(
  path.join(projectPath, 'README.md'),
  `# ${projectName}\n\nThis is a small starter project generated on ${today}.\n\n## Description\n\nA daily coding project scaffold created to help build and practice ideas consistently.\n\n## Next steps\n\n- Add project files\n- Build the project\n- Commit the initial scaffold\`
)

fs.writeFileSync(
  path.join(projectPath, 'index.js'),
  `console.log('Hello from ${projectName}!')\n`
)

console.log(`Created daily starter project at ${projectPath}`)
