type Props = {
  title: string;
  tagline: string;
  children: React.ReactNode;
};

export default function Section({ title, tagline, children }: Props) {
  return (
    <section className="mb-8">
      <h2 className="section-title">{title}</h2>
      <p className="section-tagline">{tagline}</p>
      {children}
    </section>
  );
}
