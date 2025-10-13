// src/components/LottieSafe.jsx
import Lottie from "lottie-react";

export default function LottieSafe(props) {
  const rs = { ...(props.rendererSettings || {}), viewBoxSize: false };
  return <Lottie {...props} rendererSettings={rs} />;
}
