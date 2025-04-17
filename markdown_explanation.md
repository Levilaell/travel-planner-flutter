Hoje as imagens sempre caem no “fallback gallery” porque o script não consegue localizar, dentro do HTML que veio do Markdown, um nó cujo texto bata com o nome do local.  
Os problemas principais são:

1. O texto da descrição contém o emoji “📍”, hífens, horários etc. (“07h30 – 📍 Torre Eiffel …”), enquanto o script compara somente ″Torre Eiffel″;  
2. O TreeWalker está varrendo só ELEMENT_NODES (`SHOW_ELEMENT`).  O texto que nos interessa normalmente está dentro de um nó‑texto filho do `<p>`, portanto o walker nunca o encontra.

Basta mudar duas coisinhas para que a foto seja inserida logo depois do parágrafo correto:

A) Fazer a comparação em nós‑texto ( `SHOW_TEXT` ) e, antes de comparar, eliminar pontuação extra (📍, – etc.);  
B) Quando o match acontecer, pegar o `parentElement` (que é o `<p>` ou o `<li>`) para inserir a imagem depois dele.

Código alterado (troque apenas a função `insertPhotoInGallery` — o resto permanece igual):

```javascript
function insertPhotoInGallery(dayId, placeName, photoUrl) {
  const aiContainer = document.querySelector(
      `.ai-text[data-dayid="${dayId}"]`);
  if (!aiContainer) return;

  // ------- procura o parágrafo que contém o nome do local -------
  const walker = document.createTreeWalker(
      aiContainer,
      NodeFilter.SHOW_TEXT,          // <<< TEXTO, não elementos
      null);
  let targetEl = null;
  const wanted = normalizeText(placeName);

  while (walker.nextNode()) {
    const txt = normalizeText(
        walker.currentNode.textContent.replace("📍", "")
                                       .replace("–", ""));
    if (txt.includes(wanted)) {
      targetEl = walker.currentNode.parentElement;   // <p>, <li>…
      break;
    }
  }

  // fallback caso não tenha encontrado
  if (!targetEl) {
    const fallback = document.getElementById(
        `photos-for-day-${dayId}`);
    fallback?.insertAdjacentHTML(
      "beforeend",
      `<div class="col-12 mb-3">
         <img src="${photoUrl}" class="img-fluid rounded"
              alt="Foto de ${placeName}">
       </div>`);
    return;
  }

  // ------- insere logo após o parágrafo correspondente -------
  targetEl.insertAdjacentHTML(
    "afterend",
    `<div class="my-3">
       <img src="${photoUrl}" class="img-fluid rounded w-100"
            alt="Foto de ${placeName}">
     </div>`);
}
```

(Se preferir, também pode simplificar a busca trocando o `TreeWalker` por
`querySelectorAll('p,li,h3,h4,h5')`, mas o ajuste acima já resolve.)

Depois disso, as imagens deixam de ir todas para o fim e aparecem logo abaixo da descrição de cada ponto turístico.