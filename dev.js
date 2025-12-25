const concurrently = require('concurrently');
const path = require('path');
const os = require('os');

// 1. OS 감지 및 가상환경 경로 설정
const isWin = os.platform() === 'win32';
const venvBin = isWin ? 'Scripts' : 'bin';
const pythonExec = path.join('backend', 'venv', venvBin, 'python');

// 2. 명령어 정의
const commands = [
  {
    // Backend: FastAPI
    command: `"${pythonExec}" -m uvicorn app.main:app --reload --port 8000 --app-dir backend`,
    name: 'BACKEND',
    prefixColor: 'blue',
  },
  {
    // Frontend: Next.js
    command: 'npm run dev --prefix frontend',
    name: 'FRONTEND',
    prefixColor: 'magenta',
  }
];

// 3. 실행 (concurrently)
console.log(`🚀 Starting Signal-One on ${os.platform()}...`);
console.log(`   Backend: http://localhost:8000`);
console.log(`   Frontend: http://localhost:3000`);

const { result } = concurrently(commands, {
  prefix: 'name',
  killOthers: ['failure', 'success'],
  restartTries: 0,
});

result.then(
  () => console.log('All processes stopped.'),
  () => console.log('A process stopped with an error.')
);
