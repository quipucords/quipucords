import React, { Component } from 'react';
import Masthead from './components/Masthead/Masthead'
import VerticalNavigation from './components/VerticalNavigation/VerticalNavigation'
import Content from './components/Content/Content'

import logo from './logo.svg';

import './App.css';

class App extends Component {
  render() {
    return (
      <div>
        <Masthead />
        <VerticalNavigation />
        <Content />
      </div>
    );
  }
}

export default App;
