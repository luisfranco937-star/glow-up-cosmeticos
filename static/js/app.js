/**
 * Lógica Frontend y Terminal POS para Glow Up Cosméticos.
 * Manejo de Carrito, Liquidación Impositiva, Validación de CUIT y Emisión de Factura A.
 */

// Estado del Carrito de Compras
let carrito = [];

// Formateador de moneda en pesos argentinos
function formatearMoneda(valor) {
  return "$" + valor.toLocaleString("es-AR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

// ==================== FUNCIONES DEL CARRITO Y POS ====================

function agregarAlCarrito(id, codigo, nombre, precioNeto, alicuotaIva, stockMax) {
  const itemExistente = carrito.find(item => item.id === id);

  if (itemExistente) {
    if (itemExistente.cantidad + 1 > stockMax) {
      alert(`⚠️ Stock límite alcanzado para "${nombre}". Stock disponible: ${stockMax} unidades.`);
      return;
    }
    itemExistente.cantidad += 1;
  } else {
    if (stockMax < 1) {
      alert(`⚠️ El producto "${nombre}" no posee stock disponible para la venta.`);
      return;
    }
    carrito.push({
      id: id,
      codigo: codigo,
      nombre: nombre,
      precioNeto: parseFloat(precioNeto),
      alicuotaIva: parseFloat(alicuotaIva || 21.0),
      cantidad: 1,
      stockMax: stockMax
    });
  }

  renderizarCarrito();
}

function modificarCantidad(id, delta) {
  const item = carrito.find(item => item.id === id);
  if (!item) return;

  const nuevaCantidad = item.cantidad + delta;
  if (nuevaCantidad > item.stockMax) {
    alert(`⚠️ No se puede superar el stock físico disponible (${item.stockMax} u.).`);
    return;
  }

  if (nuevaCantidad <= 0) {
    eliminarDelCarrito(id);
  } else {
    item.cantidad = nuevaCantidad;
    renderizarCarrito();
  }
}

function eliminarDelCarrito(id) {
  carrito = carrito.filter(item => item.id !== id);
  renderizarCarrito();
}

function vaciarCarrito() {
  if (carrito.length === 0) return;
  if (confirm("¿Deseas vaciar todos los productos del carrito actual?")) {
    carrito = [];
    renderizarCarrito();
  }
}

function renderizarCarrito() {
  const cartRows = document.getElementById("cartRows");
  const cartEmptyMsg = document.getElementById("cartEmptyMsg");
  const resumenNeto = document.getElementById("resumenNeto");
  const resumenIva = document.getElementById("resumenIva");
  const resumenTotal = document.getElementById("resumenTotal");

  if (!cartRows) return; // Si no estamos en la página del POS

  if (carrito.length === 0) {
    cartEmptyMsg.style.display = "block";
    cartRows.innerHTML = "";
    resumenNeto.innerText = "$0,00";
    resumenIva.innerText = "$0,00";
    resumenTotal.innerText = "$0,00";
    return;
  }

  cartEmptyMsg.style.display = "none";

  let html = "";
  let subtotalNetoAcum = 0;
  let subtotalIvaAcum = 0;

  carrito.forEach(item => {
    const netoItem = item.precioNeto * item.cantidad;
    const ivaItem = netoItem * (item.alicuotaIva / 100.0);
    const totalItem = netoItem + ivaItem;

    subtotalNetoAcum += netoItem;
    subtotalIvaAcum += ivaItem;

    html += `
      <div class="cart-item">
        <div style="flex: 1;">
          <div style="font-weight: 600; font-size: 0.85rem; color: var(--dark);">${item.nombre}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">
            Neto Unit: ${formatearMoneda(item.precioNeto)} &bull; IVA ${item.alicuotaIva}%
          </div>
          <div style="font-size: 0.8rem; font-weight: 700; color: var(--primary); margin-top: 2px;">
            Subtotal: ${formatearMoneda(netoItem)} (+ IVA: ${formatearMoneda(ivaItem)})
          </div>
        </div>

        <div style="display: flex; align-items: center; gap: 0.4rem;">
          <button type="button" class="btn btn-secondary btn-sm" style="padding: 2px 7px;" onclick="modificarCantidad(${item.id}, -1)">-</button>
          <span style="font-weight: 700; font-size: 0.9rem; min-width: 24px; text-align: center;">${item.cantidad}</span>
          <button type="button" class="btn btn-secondary btn-sm" style="padding: 2px 7px;" onclick="modificarCantidad(${item.id}, 1)">+</button>
          <button type="button" class="btn btn-outline btn-sm" style="color: var(--danger); padding: 2px 6px; margin-left: 4px;" onclick="eliminarDelCarrito(${item.id})" title="Quitar">✕</button>
        </div>
      </div>
    `;
  });

  cartRows.innerHTML = html;

  const totalAcum = subtotalNetoAcum + subtotalIvaAcum;
  resumenNeto.innerText = formatearMoneda(subtotalNetoAcum);
  resumenIva.innerText = formatearMoneda(subtotalIvaAcum);
  resumenTotal.innerText = formatearMoneda(totalAcum);
}

// ==================== VALIDACIÓN TRIBUTARIA Y CONTROL FACTURA A ====================

function alCambiarCliente() {
  const clienteSelect = document.getElementById("clienteSelect");
  if (!clienteSelect) return;

  const selectedOpt = clienteSelect.options[clienteSelect.selectedIndex];
  if (!selectedOpt) return;

  const condicion = selectedOpt.getAttribute("data-condicion");
  const cuit = selectedOpt.getAttribute("data-cuit");
  const tipoComp = document.getElementById("tipoComprobante");

  // Regla de Negocio: Si es Responsable Inscripto con CUIT, sugerir y preseleccionar FACTURA A
  if (condicion === "IVA Responsable Inscripto" && cuit) {
    tipoComp.value = "A";
  } else if (condicion === "Consumidor Final") {
    tipoComp.value = "B";
  }

  alCambiarTipoComprobante();
}

function alCambiarTipoComprobante() {
  const tipoComp = document.getElementById("tipoComprobante");
  const clienteSelect = document.getElementById("clienteSelect");
  const bannerFiscal = document.getElementById("bannerFiscal");
  const fiscalText = document.getElementById("fiscalText");
  const alertaFiscal = document.getElementById("alertaFiscalInvalida");
  const mensajeAlerta = document.getElementById("mensajeAlertaFiscal");
  const btnEmitirTexto = document.getElementById("btnEmitirTexto");
  const btnEmitirFactura = document.getElementById("btnEmitirFactura");

  if (!tipoComp || !clienteSelect) return;

  const tipo = tipoComp.value;
  const selectedOpt = clienteSelect.options[clienteSelect.selectedIndex];
  const condicion = selectedOpt ? selectedOpt.getAttribute("data-condicion") : "";
  const cuit = selectedOpt ? selectedOpt.getAttribute("data-cuit") : "";

  btnEmitirTexto.innerText = `Emitir Factura ${tipo}`;

  if (tipo === "A") {
    bannerFiscal.style.display = "block";
    fiscalText.innerHTML = `
      Comprobante oficial para clientes <strong>Responsables Inscriptos</strong> con CUIT verificado. 
      Se discrimina el <strong>Neto Gravado</strong> y la alícuota del <strong>21% de IVA</strong> para cómputo de crédito fiscal.
    `;

    // Validar si el cliente califica para Factura A
    if (condicion !== "IVA Responsable Inscripto") {
      alertaFiscal.style.display = "flex";
      mensajeAlerta.innerHTML = `
        <strong>Incompatibilidad Impositiva AFIP:</strong> No es posible emitir Factura "A" a un cliente con condición 
        <em>"${condicion}"</em>. El receptor debe ser obligatoriamente Responsable Inscripto. Selecciona <strong>Factura B</strong>.
      `;
      btnEmitirFactura.disabled = true;
      btnEmitirFactura.style.opacity = "0.5";
      btnEmitirFactura.style.cursor = "not-allowed";
    } else if (!cuit) {
      alertaFiscal.style.display = "flex";
      mensajeAlerta.innerHTML = `
        <strong>Falta CUIT:</strong> La Factura "A" exige obligatoriamente registrar un CUIT válido del cliente.
      `;
      btnEmitirFactura.disabled = true;
      btnEmitirFactura.style.opacity = "0.5";
      btnEmitirFactura.style.cursor = "not-allowed";
    } else {
      alertaFiscal.style.display = "none";
      btnEmitirFactura.disabled = false;
      btnEmitirFactura.style.opacity = "1";
      btnEmitirFactura.style.cursor = "pointer";
    }

  } else {
    // Factura B
    bannerFiscal.style.display = "block";
    fiscalText.innerHTML = `
      Comprobante para <strong>Consumidor Final</strong> o Monotributo. El precio final incluye el IVA no discriminado.
    `;
    alertaFiscal.style.display = "none";
    btnEmitirFactura.disabled = false;
    btnEmitirFactura.style.opacity = "1";
    btnEmitirFactura.style.cursor = "pointer";
  }
}

// ==================== EMISIÓN DE FACTURA (POST API) ====================

async function procesarEmisionFactura() {
  if (carrito.length === 0) {
    alert("⚠️ Debes agregar al menos un producto al carrito para emitir la factura.");
    return;
  }

  const clienteSelect = document.getElementById("clienteSelect");
  const tipoComp = document.getElementById("tipoComprobante").value;
  const metodoPago = document.getElementById("metodoPagoSelect").value;
  const observaciones = document.getElementById("obsVenta").value;
  const clienteId = parseInt(clienteSelect.value);

  const payload = {
    cliente_id: clienteId,
    tipo_comprobante: tipoComp,
    metodo_pago: metodoPago,
    observaciones: observaciones,
    items: carrito.map(item => ({
      producto_id: item.id,
      cantidad: item.cantidad
    }))
  };

  const btnEmitirFactura = document.getElementById("btnEmitirFactura");
  btnEmitirFactura.disabled = true;
  btnEmitirFactura.innerText = "⏳ Emitiendo Comprobante AFIP...";

  try {
    const response = await fetch("/api/ventas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Error al procesar la factura.");
    }

    // Éxito: Mostrar modal de confirmación fiscal
    document.getElementById("modalExitoTitulo").innerText = `¡Factura ${data.tipo_comprobante} N° ${data.numero_formateado} Emitida!`;
    document.getElementById("modalExitoDetalle").innerText = `Comprobante comercial generado correctamente para ${data.cliente_nombre}.`;
    document.getElementById("modalExitoCae").innerText = data.cae;
    document.getElementById("modalExitoCaeVto").innerText = data.cae_vto;
    document.getElementById("modalExitoTotal").innerText = formatearMoneda(data.total);

    const btnVerComprobante = document.getElementById("btnVerComprobante");
    btnVerComprobante.href = `/comprobante/${data.id}`;

    document.getElementById("modalExitoFactura").classList.add("show");

    // Vaciar carrito
    carrito = [];
    renderizarCarrito();

  } catch (error) {
    alert(`⛔ Error de Facturación: ${error.message}`);
  } finally {
    btnEmitirFactura.disabled = false;
    alCambiarTipoComprobante();
  }
}

function cerrarModalExito() {
  document.getElementById("modalExitoFactura").classList.remove("show");
  window.location.reload();
}

// ==================== BÚSQUEDA Y FILTRADO ====================

function filtrarCatalogo() {
  const query = document.getElementById("buscadorProducto").value.toLowerCase();
  const categoria = document.getElementById("filtroCategoria").value;
  const items = document.querySelectorAll(".producto-item");

  items.forEach(card => {
    const nombre = card.getAttribute("data-nombre").toLowerCase();
    const codigo = card.getAttribute("data-codigo").toLowerCase();
    const marca = card.getAttribute("data-marca").toLowerCase();
    const cat = card.getAttribute("data-categoria");

    const coincideTexto = nombre.includes(query) || codigo.includes(query) || marca.includes(query);
    const coincideCat = (categoria === "Todas" || cat === categoria);

    if (coincideTexto && coincideCat) {
      card.style.display = "block";
    } else {
      card.style.display = "none";
    }
  });
}

function filtrarTablaProductos() {
  const query = document.getElementById("buscadorTablaProductos").value.toLowerCase();
  const categoria = document.getElementById("filtroCategoriaTabla").value;
  const filas = document.querySelectorAll(".fila-producto");

  filas.forEach(fila => {
    const texto = fila.innerText.toLowerCase();
    const cat = fila.getAttribute("data-categoria");
    const coincideTexto = texto.includes(query);
    const coincideCat = (categoria === "Todas" || cat === categoria);

    fila.style.display = (coincideTexto && coincideCat) ? "" : "none";
  });
}

function filtrarClientes() {
  const query = document.getElementById("buscadorClientes").value.toLowerCase();
  const filas = document.querySelectorAll(".fila-cliente");
  filas.forEach(fila => {
    fila.style.display = fila.innerText.toLowerCase().includes(query) ? "" : "none";
  });
}

function filtrarVentas() {
  const query = document.getElementById("buscadorVentas").value.toLowerCase();
  const tipo = document.getElementById("filtroTipoVenta").value;
  const filas = document.querySelectorAll(".fila-venta");

  filas.forEach(fila => {
    const texto = fila.innerText.toLowerCase();
    const tipoVenta = fila.getAttribute("data-tipo");
    const coincideTexto = texto.includes(query);
    const coincideTipo = (tipo === "Todos" || tipoVenta === tipo);

    fila.style.display = (coincideTexto && coincideTipo) ? "" : "none";
  });
}

// ==================== VALIDADOR DE CUIT (MÓDULO 11) ====================

async function validarCuitEnVivo(cuit) {
  const msgEl = document.getElementById("cuitValidationMsg");
  if (!msgEl) return;

  const digits = cuit.replace(/\D/g, "");
  if (digits.length !== 11) {
    msgEl.innerHTML = `<span style="color: var(--text-muted);">Debe contener exactamente 11 dígitos (${digits.length}/11)</span>`;
    return;
  }

  try {
    const res = await fetch(`/api/clientes/validar-cuit?cuit=${digits}`);
    const data = await res.json();
    if (data.valido) {
      msgEl.innerHTML = `<span style="color: var(--success); font-weight: 600;">✅ CUIT Válido (${data.formateado})</span>`;
    } else {
      msgEl.innerHTML = `<span style="color: var(--danger); font-weight: 600;">❌ Dígito verificador o prefijo no válido para AFIP</span>`;
    }
  } catch (e) {
    msgEl.innerText = "";
  }
}

async function probarCuitDesdeInput() {
  const input = document.getElementById("testCuitInput");
  const resDiv = document.getElementById("testCuitResultado");
  if (!input || !resDiv) return;

  const cuit = input.value.trim();
  if (!cuit) {
    alert("Ingresa un número de CUIT para evaluar.");
    return;
  }

  try {
    const res = await fetch(`/api/clientes/validar-cuit?cuit=${cuit}`);
    const data = await res.json();
    resDiv.style.display = "block";
    if (data.valido) {
      resDiv.innerHTML = `
        <div class="alert alert-success" style="margin-bottom: 0;">
          <span>✅</span>
          <div>
            <strong>CUIT VÁLIDO SEGÚN AFIP (MÓDULO 11):</strong> ${data.formateado}.<br>
            Habilitado reglamentariamente para emisión de <strong>Factura A</strong> si la condición es Responsable Inscripto.
          </div>
        </div>
      `;
    } else {
      resDiv.innerHTML = `
        <div class="alert alert-danger" style="margin-bottom: 0;">
          <span>❌</span>
          <div>
            <strong>CUIT INVÁLIDO:</strong> El valor ingresado no supera el algoritmo de validación ponderada de AFIP.
          </div>
        </div>
      `;
    }
  } catch (e) {
    alert("Error al verificar CUIT.");
  }
}

// ==================== MODALES Y ALTAS ====================

function abrirModalNuevoCliente() {
  document.getElementById("modalNuevoCliente").classList.add("show");
}

function cerrarModalNuevoCliente() {
  document.getElementById("modalNuevoCliente").classList.remove("show");
}

function alCambiarCondicionNuevoCliente() {
  const cond = document.getElementById("newCondicionIva").value;
  const cuitInput = document.getElementById("newCuit");
  if (cond === "IVA Responsable Inscripto") {
    cuitInput.setAttribute("required", "required");
  } else {
    cuitInput.removeAttribute("required");
  }
}

async function guardarNuevoCliente(e) {
  e.preventDefault();
  const razonSocial = document.getElementById("newRazonSocial").value;
  const condicionIva = document.getElementById("newCondicionIva").value;
  const cuit = document.getElementById("newCuit").value;
  const domicilio = document.getElementById("newDomicilio").value;
  const telefono = document.getElementById("newTelefono").value;
  const email = document.getElementById("newEmail").value;

  const payload = {
    razon_social: razonSocial,
    condicion_iva: condicionIva,
    cuit: cuit || null,
    domicilio: domicilio,
    telefono: telefono,
    email: email
  };

  try {
    const response = await fetch("/api/clientes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Error al crear cliente");
    }

    alert(`✅ Cliente "${data.razon_social}" registrado exitosamente.`);
    cerrarModalNuevoCliente();
    window.location.reload();
  } catch (err) {
    alert(`⛔ ${err.message}`);
  }
}

function abrirModalNuevoProducto() {
  document.getElementById("modalNuevoProducto").classList.add("show");
}

function cerrarModalNuevoProducto() {
  document.getElementById("modalNuevoProducto").classList.remove("show");
}

async function guardarNuevoProducto(e) {
  e.preventDefault();
  const codigo = document.getElementById("prodCodigo").value;
  const nombre = document.getElementById("prodNombre").value;
  const categoria = document.getElementById("prodCategoria").value;
  const marca = document.getElementById("prodMarca").value;
  const alicuota = parseFloat(document.getElementById("prodAlicuota").value);
  const costo = parseFloat(document.getElementById("prodCosto").value);
  const neto = parseFloat(document.getElementById("prodNeto").value);
  const stock = parseInt(document.getElementById("prodStock").value);
  const stockMin = parseInt(document.getElementById("prodStockMin").value);

  const payload = {
    codigo: codigo,
    nombre: nombre,
    categoria: categoria,
    marca: marca,
    alicuota_iva: alicuota,
    precio_costo: costo,
    precio_neto: neto,
    stock_actual: stock,
    stock_minimo: stockMin
  };

  try {
    const response = await fetch("/api/productos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Error al guardar producto");
    }

    alert(`✅ Producto "${data.nombre}" registrado exitosamente.`);
    cerrarModalNuevoProducto();
    window.location.reload();
  } catch (err) {
    alert(`⛔ ${err.message}`);
  }
}

async function confirmarAnulacion(ventaId) {
  if (confirm(`¿Estás seguro de que deseas anular el comprobante ID #${ventaId}?\nEsta acción devolverá los artículos al inventario.`)) {
    try {
      const response = await fetch(`/api/ventas/${ventaId}/anular`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Error al anular");
      }
      alert(data.message);
      window.location.reload();
    } catch (err) {
      alert(`⛔ ${err.message}`);
    }
  }
}
