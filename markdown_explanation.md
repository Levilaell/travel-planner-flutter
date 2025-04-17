O problema não está no template (HTML) e sim na função JavaScript que procura o “local” no DOM para, depois, dar o insertAdjacentHTML do `<img>`.  
Atualmente ela olha a lista “day‑places‑…”, isto é, o bloco que contém apenas o nome do local e o botão 🔄 – por isso a foto vai parar ali.  
Troque a busca para o texto da descrição que está dentro da `<div class="ai‑text" …>`.

1. NO TEMPLATE (opcional)  
   Pode deixar exatamente como está. A `<div class="ai‑text" data-dayid="…">` já existe e é nela que a descrição completa é renderizada.  

2. NO JS – altere só estas duas funções:

```js
/* ---------- FOTO ---------- */
function insertPhotoInGallery(dayId, placeName, photoUrl) {
  // 1) procura a div com toda a descrição daquele dia
  const aiContainer = document.querySelector(`.ai-text[data-dayid="${dayId}"]`);
  if (!aiContainer) return;

  /* 2) percorre todos os elementos de texto dentro da descrição
        até achar o primeiro cujo texto contenha o nome do local        */
  const walker = document.createTreeWalker(aiContainer, NodeFilter.SHOW_ELEMENT, null);
  let targetEl = null;
  while (walker.nextNode()) {
    const el = walker.currentNode;
    if (textMatchesPlace(el.textContent, placeName)) {
      targetEl = el;                   // «achou» o parágrafo/cabeçalho do local
      break;
    }
  }

  // 3) se não achou, joga a foto para o “fallback gallery” no fim
  if (!targetEl) {
    const fallback = document.getElementById(`photos-for-day-${dayId}`);
    if (fallback) {
      fallback.insertAdjacentHTML(
        "beforeend",
        `<div class="col-12 mb-3">
           <img src="${photoUrl}" class="img-fluid rounded" alt="Foto de ${placeName}">
         </div>`
      );
    }
    return;
  }

  // 4) insere a imagem logo DEPOIS do elemento de texto encontrado
  targetEl.insertAdjacentHTML(
    "afterend",
    `<div class="my-3">
       <img src="${photoUrl}" class="img-fluid rounded w-100" alt="Foto de ${placeName}">
     </div>`
  );
}

/* continua igual – apenas removemos a referência a day-places‑…         */
function fetchPhotosForPlaces(dayId, placesJson, destination) {
  let places;
  try { places = JSON.parse(placesJson); } catch { return; }

  places.forEach(place => {
    const query = `${place.name}, ${destination}`;
    const cacheKey = query.toLowerCase();

    if (photoCache.has(cacheKey)) {
      insertPhotoInGallery(dayId, place.name, photoCache.get(cacheKey));
      return;
    }

    const googleUrl =
      `https://maps.googleapis.com/maps/api/place/findplacefromtext/json` +
      `?input=${encodeURIComponent(query)}` +
      `&inputtype=textquery&fields=photos&key={{ googlemaps_key }}`;

    fetch("{% url 'proxy_google_places' %}?url=" + encodeURIComponent(googleUrl))
      .then(r => r.json())
      .then(data => {
        let photoUrl;
        const ref = data.candidates?.[0]?.photos?.[0]?.photo_reference;

        photoUrl = ref
          ? "{% url 'proxy_google_photo' %}?photo_ref=" + ref
          : `https://source.unsplash.com/600x400/?${encodeURIComponent(place.name + ' ' + destination)}`;

        photoCache.set(cacheKey, photoUrl);
        insertPhotoInGallery(dayId, place.name, photoUrl);
      })
      .catch(err => console.error("Foto:", err));
  });
}
```

O resto do arquivo (loader, mapas, etc.) permanece igual.

O que mudou?

• insertPhotoInGallery agora procura o trecho de texto dentro de `.ai-text`  
• Quando encontra, faz `afterend` – a imagem fica logo após o parágrafo/cabeçalho do local, exatamente onde você queria  
• Se, por algum motivo, não encontrar o texto, cai no “fallback gallery” (o bloco `photos-for-day-…` que já existe no template).

Salve, recarregue a página e as fotos passarão a aparecer logo após a descrição de cada ponto do roteiro.