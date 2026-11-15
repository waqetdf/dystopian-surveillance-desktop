.pragma library
// One shared solver for every panel. Widths are logical pixels (Wayland scale independent).
function arrange(p, width, height) {
    const margin = 12, gap = 10;
    const W = Math.max(1, width - margin*2), H = Math.max(1, height-margin*2);
    const horizontal = W >= 660;
    if (horizontal) {
        const menuW = Math.min(326, W*0.36), sceneW = W-menuW-gap;
        const sceneH = Math.min(H, Math.max(240,sceneW*0.66));
        const menuH = Math.min(H,Math.max(sceneH,400));
        const y = Math.max(margin,Math.min(height-margin-sceneH, p.y*height));
        const my = Math.max(margin,Math.min(height-margin-menuH,y));
        const onRight = p.x+p.w/2 < .5;
        return {x:onRight?margin:margin+menuW+gap,y:y,w:sceneW,h:sceneH,
                mx:onRight?margin+sceneW+gap:margin,my:my,mw:menuW,mh:menuH};
    }
    const menuH = Math.min(H*0.48,360), sceneH = Math.max(1,H-menuH-gap);
    const below = p.y+p.h/2 < .5;
    return {x:margin,y:below?margin:margin+menuH+gap,w:W,h:sceneH,
            mx:margin,my:below?margin+sceneH+gap:margin,mw:W,mh:menuH};
}
