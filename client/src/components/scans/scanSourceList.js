import React from 'react';
import PropTypes from 'prop-types';
import { Grid, Icon } from 'patternfly-react';

class ScanSourceList extends React.Component {
  constructor() {
    super();

    this.state = {
      sources: []
    };
  }

  componentDidMount() {
    const { scan } = this.props;
    let sources = [...scan.sources];

    sources.sort((item1, item2) => {
      let cmp = item1.source_type.localeCompare(item2.source_type);
      if (cmp === 0) {
        cmp = item1.name.localeCompare(item2.name);
      }
      return cmp;
    });
    this.setState({ sources: sources });
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.scan !== this.props.scan) {
      const { scan } = this.nextProps;
      let sources = [...scan.sources];

      sources.sort((item1, item2) => {
        let cmp = item1.source_type.localeCompare(item2.source_type);
        if (cmp === 0) {
          cmp = item1.name.localeCompare(item2.name);
        }
        return cmp;
      });
      this.setState({ sources: sources });
    }
  }

  renderSourceIcon(source) {
    switch (source.source_type) {
      case 'vcenter':
        return <Icon type="pf" name="virtual-machine" />;
      case 'network':
        return <Icon type="pf" name="network" />;
      case 'satellite':
        return <Icon type="fa" name="space-shuttle" />;
      default:
        return null;
    }
  }

  render() {
    const { sources } = this.state;

    return (
      <Grid fluid>
        {sources.map((item, index) => (
          <Grid.Row key={index}>
            <Grid.Col xs={12} sm={4}>
              <span>
                {this.renderSourceIcon(item)}
                &nbsp; {item.name}
              </span>
            </Grid.Col>
          </Grid.Row>
        ))}
      </Grid>
    );
  }
}

ScanSourceList.propTypes = {
  scan: PropTypes.object
};

export { ScanSourceList };
