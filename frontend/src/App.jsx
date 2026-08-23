import { useState, useEffect, useCallback } from "react";
import { api } from "./api/client";
import { useProducts } from "./hooks/useProducts";
import { useProduct } from "./hooks/useProduct";
import Topbar from "./components/Topbar";
import Sidebar from "./components/Sidebar";
import ProductDetail from "./components/ProductDetail";
import IngestModal from "./components/IngestModal";
import { ToastProvider, useToast } from "./components/Toast";
import Login from "./components/Login";
import LandingPage from "./components/LandingPage";

function AppInner() {
  const toast = useToast();
  const [apiOk, setApiOk] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('veritas_token'));
  const [demoRunning, setDemoRunning] = useState(false);
  const [showIngest, setShowIngest] = useState(false);
  const [showLanding, setShowLanding] = useState(true);

  const { products, loading: productsLoading, refresh: refreshProducts } = useProducts();
  const { product, loading: productLoading, load: loadProduct, setProduct, review } = useProduct();

  // Check API health on mount
  useEffect(() => {
    api.health()
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false));
  }, []);

  const handleRunDemo = useCallback(async () => {
    setDemoRunning(true);
    try {
      let result;
      try {
        result = await api.runDemo();
      } catch (err) {
        // Direct ingest fallback with the 3 demo sources
        result = await api.ingest({
          product_name: "SIMATIC S7-1200 CPU 1214C",
          product_id: "6ES7214-1AG40-0XB0",
          sources: [
            {
              source_id: "source_a",
              source_type: "datasheet",
              format: "text",
              raw_content: `SIEMENS SIMATIC S7-1200 CPU 1214C\nTechnical Datasheet — Document No. 6ES7214-1AG40-0XB0\nPage 24 — Technical specifications\n\nSupply voltage: rated 24 V DC, operating range 20.4 V DC to 28.8 V DC\nDigital inputs: 14 x 24 V DC\nDigital outputs: 10 x relay, 2 A\nWeight: approximately 1.35 kg (including front connectors)\nAmbient temperature during operation: -20 C to +60 C\nDegree of protection: IP20\nWork memory: 100 KB\nCommunication: PROFINET, Ethernet\nDimensions (W x H x D): 110 mm x 100 mm x 75 mm`
            },
            {
              source_id: "source_b",
              source_type: "manufacturer_website",
              format: "text",
              raw_content: `Product page — siemens.com/simatic-s7-1200\nSIMATIC S7-1200, CPU 1214C\n\nCompact PLC for small to medium automation tasks.\nInput voltage: 24V DC\nWeight: 1.2 kg\nOperating temperature: -20C to 60C\nProtection class: IP20\nDigital I/O: 14 DI / 10 DO\nEthernet interface: yes, PROFINET supported\nMemory: 100 KB work memory\n\nBuy now or find a distributor near you.`
            },
            {
              source_id: "source_c",
              source_type: "distributor_erp",
              format: "csv",
              raw_content: `sku,description,voltage,weight_kg,temp_range,protection,memory_kb\n6ES7214-1AG40-0XB0,SIMATIC S7-1200 CPU 1214C PLC,24VDC,1.4,-20 to 55 C,IP20,100`
            }
          ]
        });
      }
      await refreshProducts();
      await loadProduct(result.product_id);
      window.history.pushState({ view: "product", id: result.product_id }, "", `#${result.product_id}`);
      toast("Demo pipeline complete!", "success");
    } catch (e) {
      toast(`Error: ${e.message}`, "error");
    } finally {
      setDemoRunning(false);
    }
  }, [refreshProducts, loadProduct, toast]);

  const handleSelectProduct = useCallback(
    async (id) => {
      await loadProduct(id);
      window.history.pushState({ view: "product", id }, "", `#${id}`);
    },
    [loadProduct]
  );

  // Handle browser back/forward
  useEffect(() => {
    const onPop = () => {
      setProduct(null);
      window.history.replaceState({ view: "home" }, "", window.location.pathname);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [setProduct]);

  const handleReview = useCallback(
    async (attribute, action, correctedValue) => {
      try {
        await review(attribute, action, correctedValue);
        await refreshProducts();
        toast(
          `Attribute "${attribute.replace(/_/g, " ")}" ${action === "edit" ? "updated" : action + "d"}.`,
          action === "reject" ? "error" : "success"
        );
      } catch (e) {
        toast(`Review failed: ${e.message}`, "error");
      }
    },
    [review, refreshProducts, toast]
  );

  const handleIngestSuccess = useCallback(
    async (result) => {
      await refreshProducts();
      await loadProduct(result.product_id);
      window.history.pushState({ view: "product", id: result.product_id }, "", `#${result.product_id}`);
      toast(`"${result.product_name}" processed successfully.`, "success");
    },
    [refreshProducts, loadProduct, toast]
  );

  // Show landing page first
  if (showLanding) {
    return <LandingPage onEnterApp={() => setShowLanding(false)} />;
  }

  if (!token) {
    return <Login onLogin={setToken} />;
  }

  return (
    <div className="app-shell">
      <Topbar
        apiOk={apiOk}
        onRunDemo={handleRunDemo}
        running={demoRunning}
        onOpenIngest={() => setShowIngest(true)}
        onHome={() => { setProduct(null); setShowLanding(true); }}
      />

      <div className="main-layout">
        <Sidebar
          products={products}
          loading={productsLoading}
          activeId={product?.product_id}
          onSelect={handleSelectProduct}
        />
        <ProductDetail
          product={product}
          loading={productLoading}
          onReview={handleReview}
          onOpenIngest={() => setShowIngest(true)}
          onRunDemo={handleRunDemo}
          onBack={() => {
            setProduct(null);
            window.history.back();
          }}
        />
      </div>

      {showIngest && (
        <IngestModal
          onClose={() => setShowIngest(false)}
          onSuccess={handleIngestSuccess}
        />
      )}
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppInner />
    </ToastProvider>
  );
}

