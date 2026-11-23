(() => {
  const focusClock = document.querySelector('#focus-clock');
  if (focusClock) {
    const duration = document.querySelector('#focus-duration');
    const task = document.querySelector('#focus-task');
    const status = document.querySelector('#focus-status');
    const startButton = document.querySelector('#focus-start');
    const pauseButton = document.querySelector('#focus-pause');
    const resetButton = document.querySelector('#focus-reset');
    let remaining = Number(duration.value) * 60;
    let interval = null;

    const renderTime = () => {
      const minutes = Math.floor(remaining / 60);
      const seconds = remaining % 60;
      focusClock.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
      focusClock.setAttribute('aria-label', `${minutes} minutes and ${seconds} seconds remaining`);
    };

    const stopTimer = () => {
      window.clearInterval(interval);
      interval = null;
      startButton.disabled = false;
      pauseButton.disabled = true;
      duration.disabled = false;
    };

    startButton.addEventListener('click', () => {
      if (interval !== null) return;
      if (!task.value.trim()) {
        status.textContent = 'Add one small task to give this sprint a clear target.';
        task.focus();
        return;
      }
      if (remaining <= 0) remaining = Number(duration.value) * 60;
      status.textContent = `Working on: ${task.value.trim()}`;
      startButton.disabled = true;
      pauseButton.disabled = false;
      duration.disabled = true;
      interval = window.setInterval(() => {
        remaining -= 1;
        renderTime();
        if (remaining <= 0) {
          stopTimer();
          status.textContent = 'Sprint complete. Take a short break, then decide whether to continue.';
        }
      }, 1000);
    });

    pauseButton.addEventListener('click', () => {
      if (interval === null) return;
      stopTimer();
      status.textContent = 'Paused. Resume when you are ready.';
    });

    resetButton.addEventListener('click', () => {
      stopTimer();
      remaining = Number(duration.value) * 60;
      renderTime();
      status.textContent = 'Timer reset. Ready when you are.';
    });

    duration.addEventListener('change', () => {
      remaining = Number(duration.value) * 60;
      renderTime();
      status.textContent = 'Session length updated.';
    });

    renderTime();
  }

  const form = document.querySelector('#prediction-form');
  if (form) {
    form.addEventListener('submit', event => {
      let valid = true;
      form.querySelectorAll('.field').forEach(field => {
        const control = field.querySelector('input, select');
        const error = field.querySelector('.field-error');
        let message = '';
        if (!control.value.trim()) message = 'Please enter or choose a value.';
        else if (control.type === 'number' && !Number.isFinite(Number(control.value))) message = 'Enter a valid number.';
        else if (control.type === 'number' && (Number(control.value) < Number(control.min) || Number(control.value) > Number(control.max))) message = `Use a value from ${control.min} to ${control.max}.`;
        else if (control.type === 'number' && control.step === '1' && !Number.isInteger(Number(control.value))) message = 'Enter a whole number.';
        error.textContent = message;
        field.classList.toggle('invalid', Boolean(message));
        if (message) valid = false;
      });
      if (!valid) { event.preventDefault(); return; }
      form.classList.add('is-loading');
      form.querySelector('button').disabled = true;
    });
    form.querySelectorAll('input, select').forEach(control => control.addEventListener('input', () => {
      const field = control.closest('.field');
      field.classList.remove('invalid');
      field.querySelector('.field-error').textContent = '';
    }));
  }
  const data = window.dashboardData;
  if (data && window.Chart) {
    const mapping = [
      ['study-chart', 'study_hours_per_day', 'Study hours/day'],
      ['sleep-chart', 'sleep_hours_per_night', 'Sleep/night (hours)'],
      ['screen-chart', 'screen_time_hours_per_day', 'Screen time/day']
    ];
    mapping.forEach(([id, key, xLabel]) => {
      const canvas = document.getElementById(id);
      if (!canvas) return;
      const points = data[key] || [];
      if (!points.length) { canvas.hidden = true; canvas.nextElementSibling.hidden = false; return; }
      new Chart(canvas, {
        type: 'scatter',
        data: {datasets: [{data: points, backgroundColor: 'rgba(86, 142, 255, .62)', borderColor: 'rgba(86, 142, 255, .8)', pointRadius: 3}]},
        options: {responsive: true, maintainAspectRatio: false,
          plugins: {legend: {display: false}, tooltip: {callbacks: {label: item => `${xLabel}: ${item.raw.x.toFixed(1)} · Stress: ${item.raw.y.toFixed(1)}`}}},
          scales: {x: {title: {display: true, text: xLabel}, grid: {color: 'rgba(148,163,184,.09)'}, ticks: {color: '#8793a8'}},
            y: {title: {display: true, text: 'Reported stress level'}, min: 1, max: 10, grid: {color: 'rgba(148,163,184,.09)'}, ticks: {color: '#8793a8'}}}}
      });
    });
  }
})();
