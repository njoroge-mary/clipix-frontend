import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Video, Scissors, Sparkles, Zap } from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Video,
      title: 'Video Editing',
      description: 'Professional-grade video editing tools at your fingertips'
    },
    {
      icon: Scissors,
      title: 'Easy Trimming',
      description: 'Cut and trim your videos with precision'
    },
    {
      icon: Sparkles,
      title: 'Effects & Filters',
      description: 'Add stunning effects and filters to your videos'
    },
    {
      icon: Zap,
      title: 'Fast Processing',
      description: 'Lightning-fast rendering and export'
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Video className="h-8 w-8 text-primary" />
            <h1 className="text-2xl font-bold">Clipix</h1>
            <Badge variant="secondary">Beta</Badge>
          </div>
          <Button onClick={() => navigate('/dashboard')} data-testid="get-started-btn">
            Get Started
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="text-5xl font-bold mb-6" data-testid="hero-title">
            Video Editing Made Simple
          </h2>
          <p className="text-xl text-muted-foreground mb-8" data-testid="hero-description">
            Create stunning videos with our powerful yet easy-to-use video editing platform.
            Professional results without the complexity.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" onClick={() => navigate('/dashboard')} data-testid="cta-start-editing">
              Start Editing Now
            </Button>
            <Button size="lg" variant="outline" data-testid="cta-learn-more">
              Learn More
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16 bg-muted/50">
        <div className="text-center mb-12">
          <h3 className="text-3xl font-bold mb-4">Powerful Features</h3>
          <p className="text-muted-foreground">Everything you need to create amazing videos</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <Card key={index} data-testid={`feature-card-${index}`}>
              <CardHeader>
                <feature.icon className="h-12 w-12 mb-4 text-primary" />
                <CardTitle>{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{feature.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <Card className="bg-primary text-primary-foreground">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl mb-4">Ready to Create?</CardTitle>
            <CardDescription className="text-primary-foreground/80 text-lg">
              Join thousands of creators who trust Clipix for their video editing needs
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <Button 
              size="lg" 
              variant="secondary" 
              onClick={() => navigate('/dashboard')}
              data-testid="cta-get-started-bottom"
            >
              Get Started Free
            </Button>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t mt-20">
        <div className="container mx-auto px-4 py-8 text-center text-muted-foreground">
          <p>© 2025 Clipix. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
