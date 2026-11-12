import Image from "next/image";
import Link from "next/link";

type BrandLogoProps = {
  href?: string;
  compact?: boolean;
  showWordmark?: boolean;
  className?: string;
};

export function BrandLogo({
  href = "/overview",
  compact = false,
  showWordmark = true,
  className = ""
}: BrandLogoProps) {
  const content = (
    <>
      <span className={`brandLogoMark ${compact ? "compact" : ""}`}>
        <Image
          src="/athena-logo.png"
          alt="Athena"
          width={compact ? 84 : 192}
          height={compact ? 84 : 192}
          priority
          className="brandLogoImage"
        />
      </span>
      {showWordmark && (
        <span className="brandText">
          Athena
          {!compact && <small className="brandTagline">Dare more and rise above</small>}
        </span>
      )}
    </>
  );

  if (!href) {
    return <span className={`brand ${className}`.trim()}>{content}</span>;
  }

  return (
    <Link href={href} className={`brand ${className}`.trim()} aria-label="Athena home">
      {content}
    </Link>
  );
}
