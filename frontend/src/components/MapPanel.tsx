"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { assetUrl } from "@/lib/api";
import type { MapDetail } from "@/lib/types";
import { ValuesTable } from "./ValuesTable";

function EnlargedMap({ title, src, onClose }: { title: string; src: string; onClose: () => void }) {
  const closeButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeButton.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div className="modal" role="dialog" aria-modal="true" aria-label={title} onClick={onClose}>
      <div className="modal__content" onClick={(event) => event.stopPropagation()}>
        <button ref={closeButton} type="button" className="button modal__close" onClick={onClose}>
          Close
        </button>
        <Image
          src={src}
          alt={title}
          width={224}
          height={224}
          unoptimized
          className="modal__image"
        />
      </div>
    </div>
  );
}

export function MapPanel({ map }: { map: MapDetail }) {
  const [open, setOpen] = useState(false);
  const src = assetUrl(map.image_url);
  return (
    <figure className="map">
      <button
        type="button"
        className="map__button"
        onClick={() => setOpen(true)}
        aria-label={`Enlarge ${map.title}`}
      >
        <Image
          src={src}
          alt={map.title}
          width={224}
          height={224}
          unoptimized
          className="map__image"
        />
      </button>
      <figcaption>{map.title}</figcaption>
      <ValuesTable values={map.values} unit={map.unit} />
      {open && <EnlargedMap title={map.title} src={src} onClose={() => setOpen(false)} />}
    </figure>
  );
}
