import { useState, useCallback } from "react";
import { api } from "../api/client";

export function useProduct() {
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getProduct(id);
      setProduct(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const review = useCallback(
    async (attribute, action, correctedValue) => {
      if (!product) return;
      const payload = { attribute, action };
      if (correctedValue !== undefined) payload.corrected_value = correctedValue;
      const updated = await api.reviewAttribute(product.product_id, payload);
      setProduct(updated);
      return updated;
    },
    [product]
  );

  return { product, loading, error, load, setProduct, review };
}
