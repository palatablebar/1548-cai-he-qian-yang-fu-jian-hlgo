function renderVisual(target, data) {
    const byMachine = new Map();
    for (const row of data.rows) {
        if (!byMachine.has(row.zone)) byMachine.set(row.zone,[]);
        byMachine.get(row.zone).push(row.estimate);
    }
    const ledger = node('div',undefined,'register-lines');
    for (const [name, scores] of byMachine) {
        const average = scores.reduce((a,b) => a+b,0)/scores.length;
        const band = node('div',undefined,'register-row');
        const strip = node('div',undefined,'pigment-strip');
        strip.style.width = `${Math.max(5,average*100)}%`;
        band.append(node('strong',name),strip,node('output',`${Math.round(average*100)}%`));
        ledger.append(band);
    }
    target.append(ledger);
}
