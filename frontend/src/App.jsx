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
  const { product, loading: productLoading, load: loadProduct, review } = useProduct();

  // Check API health on mount
  useEffect(() => {
    api.health()
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false));
  }, []);

  const handleRunDemo = useCallback(async () => {
    setDemoRunning(true);
    try {
      const result = await api.runDemo();
      await refreshProducts();
      await loadProduct(result.product_id);
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
    },
    [loadProduct]
  );

  const handleReview = useCallback(
    async (attribute, action) => {
      try {
        await review(attribute, action);
        await refreshProducts();
        toast(
          `Attribute "${attribute.replace(/_/g, " ")}" ${action}d.`,
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

