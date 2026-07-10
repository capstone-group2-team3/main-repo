import { ImageResponse } from "next/og";

export const size = {
  width: 64,
  height: 64,
};

export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          alignItems: "center",
          background: "linear-gradient(135deg,#0F172A 0%,#164E63 52%,#0F766E 100%)",
          borderRadius: "18px",
          color: "white",
          display: "flex",
          height: "64px",
          justifyContent: "center",
          position: "relative",
          width: "64px",
        }}
      >
        <div
          style={{
            border: "3px solid rgba(255,255,255,.92)",
            borderRadius: "14px",
            height: "42px",
            position: "absolute",
            width: "42px",
          }}
        />
        <svg width="46" height="24" viewBox="0 0 46 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M2 12H10L14 5L20 21L26 3L31 12H44"
            stroke="white"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    ),
    size,
  );
}
