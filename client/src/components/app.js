import React, { Component } from 'react';
import Masthead from './masthead/masthead';
import VerticalNavigation from './verticalNavigation/verticalNavigation';
import Content from './content/content';
import { routes } from '../routes';
import './app.css';

class App extends Component {
  constructor() {
    super();
    this.menu = routes();
  }

  render() {
    return [
      <Masthead key="masthead" />,
      <VerticalNavigation menuItems={this.menu} key="navigation" />,
      <Content key="content" />
    ];
  }
}

export default App;
