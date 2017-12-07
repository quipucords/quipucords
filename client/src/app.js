import React, { Component } from 'react';
import Masthead from './components/masthead/masthead'
import VerticalNavigation from './components/verticalNavigation/verticalNavigation'
import { getMenu } from './routes'

import './app.css';
import Content from "./components/content/content";

class App extends Component {
  constructor() {
    super();
    this.menu = getMenu();
  }

  render() {
    return (
      <div>
        <Masthead />
        <VerticalNavigation menuItems={this.menu}/>
        <Content/>
      </div>
    );
  }
}

export default App;
