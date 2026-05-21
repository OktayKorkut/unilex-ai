import { useRef, useState, useEffect } from 'react';
import { Box, Title, Text, Button, Container, Flex } from '@mantine/core';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import classes from './Hero.module.css';

gsap.registerPlugin(useGSAP);

const sequenceTexts = [
  "Meet UniLex",
  "Stop searching",
  "Stop scrolling",
  "Forget the chaos",
  "It crawls. It learns. It updates.",
  "Zero Hallucination",
  "100% Citation",
  "No assumptions",
  "Only pure academic facts",
];

export default function Hero() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mainTitleRef = useRef<HTMLDivElement>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem('token'));
  }, []);

  const handleStart = () => {
    if (localStorage.getItem('token')) {
      navigate('/chat');
    } else {
      window.dispatchEvent(new Event('open-auth-modal'));
    }
  };

  useGSAP(() => {
    const tl = gsap.timeline();

    // Loop through each text and animate it
    sequenceTexts.forEach((_, index) => {
      const target = `.seqText-${index}`;

      tl.fromTo(target,
        { opacity: 0, scale: 0.8, filter: 'blur(10px)' },
        { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.8, ease: 'power2.out' }
      )
        .to(target,
          { opacity: 0, scale: 1.1, filter: 'blur(10px)', duration: 0.6, ease: 'power2.in', delay: 0.8 }
        );
    });

    // Final Reveal of the main content
    tl.fromTo(mainTitleRef.current,
      { opacity: 0, y: 50, filter: 'blur(10px)' },
      { opacity: 1, y: 0, filter: 'blur(0px)', duration: 1.5, ease: 'back.out(1.7)' }
    );

  }, { scope: containerRef });

  return (
    <Box className={classes.heroWrapper} ref={containerRef}>
      {/* Animated Background Elements */}
      <div className={classes.gridBackground}></div>
      <div className={classes.glow}></div>
      <div className={classes.glow2}></div>
      <div className={classes.glow3}></div>
      <div className={classes.ring1}></div>
      <div className={classes.ring2}></div>

      <Container size="xl" h="100%">
        <Flex direction="column" justify="center" align="center" h="100%" pos="relative">

          {/* Render all sequence texts, they are absolute positioned and hidden by default */}
          {sequenceTexts.map((text, index) => (
            <Title
              key={index}
              order={2}
              className={`${classes.seqText} seqText-${index}`}
            >
              {text}
            </Title>
          ))}

          {/* Final Content to Reveal */}
          <Box className={classes.mainContent} ref={mainTitleRef}>
            <Title order={1} className={classes.mainTitle}>
              Bilginin Işığında <br /> <span className={classes.highlight}>Akademik Derinlik.</span>
            </Title>
            <Text c="dimmed" size="xl" mt="xl" maw={600} mx="auto" ta="center">
              RAG teknolojisiyle güçlendirilmiş UniLex ile akademik kaynaklarınızı saniyeler içinde tarayın, sentezleyin ve bilimsel doğrulukla raporlayın.
            </Text>
            <Flex justify="center" gap="md" mt={40} direction={{ base: 'column', sm: 'row' }} align={{ base: 'stretch', sm: 'center' }} px={{ base: 'md', sm: 0 }} maw={450} mx="auto">
              <Button size="xl" radius="xl" variant="filled" color="cyan" className={classes.actionBtn} onClick={handleStart}>
                {isLoggedIn ? 'Asistana Git' : 'Ücretsiz Başla'}
              </Button>
              <Button size="xl" radius="xl" variant="outline" color="cyan" className={classes.actionBtn} component="a" href="/#features">
                Özellikleri İncele
              </Button>
            </Flex>
          </Box>
        </Flex>
      </Container>
    </Box>
  );
}
