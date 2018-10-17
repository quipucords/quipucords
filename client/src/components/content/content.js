import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { routes } from '../../routes';

class Content extends React.Component {
  static renderRoutes() {
    let redirectRoot = null;

    return {
      renderRoutes: routes().map(item => {
        if (item.redirect === true) {
          redirectRoot = <Redirect from="/" to={item.to} />;
        }

        return <Route key={item.to} path={item.to} component={item.component} />;
      }),
      redirectRoot
    };
  }

  render() {
    const { renderRoutes, redirectRoot } = Content.renderRoutes();

    return (
      <div className="quipucords-content">
        <Switch>
          {renderRoutes}
          {redirectRoot}
        </Switch>
      </div>
    );
  }
}

export { Content as default, Content };
