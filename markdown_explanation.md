Para injetar a foto logo após o parágrafo (ou título, ou trecho) que descreve cada lugar — e não mais dentro da listagem de “editar lugares” — precisamos:

 1. **No template**:  
    • Manter o `data-dayid` em `.ai-text` (já está) para sabermos em que dia estamos.  
    • Remover (ou deixar só como _backup_) o container `#day-places-{{ d.id }}` como zona de holding do JSON, mas não usá‑lo para render de fotos.  

    Ficaria algo assim, simplificado (só o trecho relevante):
    
    ```html
    <div class="result-card mb-3">
      <div class="ai-text" data-dayid="{{ d.id }}">
        {{ d.generated_text|markdownify|safe }}
      </div>
      <!-- container que guarda o JSON, mas sem exibir nada -->
      <div id="day-places-{{ d.id }}" data-places='{{ d.places_visited|safe }}' style="display:none;"></div>
    </div>
    ```
    
 2. **No JavaScript**:  
    Substituir a lógica de busca e inserção de fotos dentro da listagem por uma lógica que:
    
    a) Recupere o JSON de `places_visited` via `data-places` no `#day-places-{{ d.id }}`.  
    b) Para cada lugar, procure dentro da `div.ai-text[data-dayid="…"]` o elemento (p, h3, li, whatever) cujo texto contenha o nome do lugar.  
    c) Insira ali, **logo após** esse elemento, a `<img>` com a foto.  

    Exemplo de código (substitua suas funções `insertPhotoInGallery` e `fetchPhotosForPlaces` por algo como isto):  

    ```js
    // normalização e cache podem ficar como estão
    const photoCache = new Map();

    function normalizeText(str) {
      return (str||"")
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .replace(/[^\w\s]/g, " ")
        .toLowerCase()
        .trim();
    }

    function insertPhotoAfterDescription(dayId, placeName, photoUrl) {
      const aiText = document.querySelector(`.ai-text[data-dayid="${dayId}"]`);
      if (!aiText) return;

      // procuramos qualquer parágrafo, título ou li que fale do placeName
      const candidates = Array.from(aiText.querySelectorAll("p, h1, h2, h3, li"));
      for (let el of candidates) {
        if ( normalizeText(el.textContent).includes(normalizeText(placeName)) ) {
          // inserimos logo após esse el
          el.insertAdjacentHTML(
            "afterend",
            `<div class="place-photo-wrapper text-center my-3">
               <img src="${photoUrl}"
                    class="img-fluid rounded"
                    alt="Foto de ${placeName}"
                    style="max-height:200px;">
             </div>`
          );
          return;
        }
      }
      // se não encontrar parágrafo, podemos anexar ao final do aiText:
      aiText.insertAdjacentHTML(
        "beforeend",
        `<div class="place-photo-wrapper text-center my-3">
           <img src="${photoUrl}"
                class="img-fluid rounded"
                alt="Foto de ${placeName}"
                style="max-height:200px;">
         </div>`
      );
    }

    function fetchPhotosForPlaces(dayId, placesJson, destination) {
      let places;
      try { places = JSON.parse(placesJson); } catch { return; }

      places.forEach(place => {
        const query = `${place.name}, ${destination}`;
        const key = query.toLowerCase();

        if (photoCache.has(key)) {
          return insertPhotoAfterDescription(dayId, place.name, photoCache.get(key));
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
            if (ref) {
              photoUrl = "{% url 'proxy_google_photo' %}?photo_ref=" + ref;
            } else {
              photoUrl =
                `https://source.unsplash.com/600x400/?${encodeURIComponent(place.name + ' ' + destination)}`;
            }
            photoCache.set(key, photoUrl);
            insertPhotoAfterDescription(dayId, place.name, photoUrl);
          })
          .catch(console.error);
      });
    }

    // dispara quando o modal abre
    document.querySelectorAll(".modal.fade").forEach(modal => {
      modal.addEventListener("shown.bs.modal", () => {
        const itinId = modal.id.replace("modalIt", "");
        // demais init de mapa...

        modal.querySelectorAll('[id^="day-places-"]').forEach(div => {
          const dayId = div.id.replace("day-places-", "");
          const raw = div.dataset.places;
          if (raw) {
            // título do modal tem o destino
            const destination =
              modal.querySelector(".modal-title")?.textContent.split(" - ")[0] || "";
            fetchPhotosForPlaces(dayId, raw, destination);
          }
        });
      });
    });
    ```

 3. **Resumo**  
    - No HTML: não use mais o container que exibia as fotos no final da listagem de edição, mas mantenha o `data-places` guardando o JSON.  
    - No JS: troque a função de inserção de fotos (`insertPhotoInGallery`) por uma que procure dentro do `.ai-text` e injete a foto **logo após** o parágrafo/título que menciona o nome do lugar.  

Dessa forma cada `[Foto …]` aparecerá imediatamente após a descrição gerada daquele ponto, igual ao exemplo que você quer.