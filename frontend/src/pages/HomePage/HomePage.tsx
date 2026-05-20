import Hero from '../../components/Hero/Hero';
import Features from '../../components/Features/Features';
import HowItWorks from '../../components/HowItWorks/HowItWorks';
import Footer from '../../components/Footer/Footer';
import { Box } from '@mantine/core';

export default function HomePage() {
  return (
    <Box>
      <Hero />
      <Features />
      <HowItWorks />
      <Footer />
    </Box>
  );
}
