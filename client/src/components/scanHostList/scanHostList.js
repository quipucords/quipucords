import React from 'react';
import PropTypes from 'prop-types';
import InfiniteScroll from 'react-infinite-scroller';
import { connect } from 'react-redux';
import { EmptyState, Grid } from 'patternfly-react';
import _ from 'lodash';
import { helpers } from '../../common/helpers';
import { dictionary } from '../../constants/dictionaryConstants';
import { reduxActions } from '../../redux/actions';

class ScanHostList extends React.Component {
  constructor() {
    super();

    this.state = {
      scanResults: [],
      scanResultsError: false,
      connectionScanResultsPending: false,
      inspectionScanResultsPending: false,
      moreResults: false,
      prevResults: []
    };

    this.loading = false;
  }

  componentDidMount() {
    this.refresh(this.props);
  }

  componentWillReceiveProps(nextProps) {
    const { lastRefresh, status, useConnectionResults, useInspectionResults } = this.props;
    // Check for changes resulting in a fetch
    if (
      !_.isEqual(nextProps.lastRefresh, lastRefresh) ||
      nextProps.status !== status ||
      nextProps.useConnectionResults !== useConnectionResults ||
      nextProps.useInspectionResults !== useInspectionResults
    ) {
      this.refresh(nextProps);
    }
  }

  onLoadMore = page => {
    if (this.loading) {
      return;
    }

    this.loading = true;
    this.refresh(this.props, page);
  };

  getInspectionResults(passedPage, status) {
    const { scanId, sourceId, getInspectionScanResults, useConnectionResults, useInspectionResults } = this.props;
    const { connectionScanResultsPending, page, prevResults } = this.state;
    const fetchAll = useConnectionResults && useInspectionResults;

    const queryObject = {
      page: passedPage === undefined ? page : passedPage,
      page_size: 100,
      ordering: 'name',
      status
    };

    if (sourceId) {
      queryObject.source_id = sourceId;
    }

    getInspectionScanResults(scanId, queryObject)
      .then(results => {
        const morePages = fetchAll && _.get(results.value, 'data.next') !== null;

        this.setState({
          inspectionScanResultsPending: morePages,
          scanResults: this.addResults(results),
          prevResults: morePages || connectionScanResultsPending ? prevResults : []
        });
        this.loading = connectionScanResultsPending;

        if (morePages) {
          this.getInspectionResults(passedPage + 1, status);
        }
      })
      .catch(error => {
        this.setState({
          inspectionScanResultsPending: false,
          scanResultsError: helpers.getMessageFromResults(error).message
        });
      });
  }

  getConnectionResults(passedPage, status) {
    const { scanId, sourceId, getConnectionScanResults, useConnectionResults, useInspectionResults } = this.props;
    const { inspectionScanResultsPending, page, prevResults } = this.state;
    const usePaging = !useConnectionResults || !useInspectionResults;

    const queryObject = {
      page: passedPage === undefined ? page : passedPage,
      page_size: 100,
      ordering: 'name',
      status
    };

    if (sourceId) {
      queryObject.source_id = sourceId;
    }

    getConnectionScanResults(scanId, queryObject)
      .then(results => {
        const allResults = this.addResults(results);
        const morePages = _.get(results.value, 'data.next') !== null;

        this.setState({
          moreResults: morePages,
          connectionScanResultsPending: morePages && !usePaging,
          scanResults: allResults,
          prevResults: morePages || inspectionScanResultsPending ? prevResults : []
        });
        this.loading = inspectionScanResultsPending;

        if (morePages && !usePaging) {
          this.getConnectionResults(passedPage + 1, status);
        }
      })
      .catch(error => {
        this.setState({
          connectionScanResultsPending: false,
          scanResultsError: helpers.getMessageFromResults(error).message
        });
      });
  }

  addResults(results) {
    const { scanResults } = this.state;
    const { useConnectionResults, useInspectionResults } = this.props;

    const newResults = _.get(results, 'value.data.results', []);
    const allResults = [...scanResults, ...newResults];

    if (useConnectionResults && useInspectionResults) {
      allResults.sort((item1, item2) => {
        if (helpers.isIpAddress(item1.name) && helpers.isIpAddress(item2.name)) {
          const value1 = helpers.ipAddressValue(item1.name);
          const value2 = helpers.ipAddressValue(item2.name);

          return value1 - value2;
        }

        return item1.name.localeCompare(item2.name);
      });
    }

    return allResults;
  }

  refresh(useProps, page = 1) {
    const { useConnectionResults, useInspectionResults, status } = useProps;
    const { scanResults } = this.state;

    this.setState({
      connectionScanResultsPending: useConnectionResults,
      inspectionScanResultsPending: useInspectionResults,
      scanResults: page === 1 ? [] : scanResults,
      prevResults: scanResults,
      moreResults: false
    });
    this.loading = true;

    if (useConnectionResults) {
      this.getConnectionResults(page, status);
    }

    if (useInspectionResults) {
      this.getInspectionResults(page, status);
    }
  }

  renderResults(results) {
    const { renderHostRow } = this.props;
    const { moreResults } = this.state;

    if (_.size(results) === 0) {
      return null;
    }

    const rowItems = results.map(host => (
      <Grid.Row key={`${host.name}-${host.source.id}`}>{renderHostRow(host)}</Grid.Row>
    ));

    const loader = (
      <div key="loader" className="loader">
        Loading...
      </div>
    );

    return (
      <div className="host-results">
        <Grid fluid className="host-list">
          <InfiniteScroll
            pageStart={1}
            loadMore={this.onLoadMore}
            hasMore={moreResults}
            useWindow={false}
            loader={loader}
          >
            {rowItems}
          </InfiniteScroll>
        </Grid>
      </div>
    );
  }

  render() {
    const { status, useConnectionResults, useInspectionResults } = this.props;
    const {
      scanResults,
      connectionScanResultsPending,
      inspectionScanResultsPending,
      scanResultsError,
      prevResults
    } = this.state;
    const usePaging = !useConnectionResults || !useInspectionResults;

    if ((!_.size(scanResults) || !usePaging) && (inspectionScanResultsPending || connectionScanResultsPending)) {
      return (
        <React.Fragment>
          <EmptyState>
            <EmptyState.Icon name="spinner spinner-xl" />
            <EmptyState.Title>Loading scan results...</EmptyState.Title>
          </EmptyState>
          <div className="hidden-results">{this.renderResults(prevResults)}</div>
        </React.Fragment>
      );
    }

    if (scanResultsError) {
      return (
        <EmptyState>
          <EmptyState.Icon name="error-circle-o" />
          <EmptyState.Title>Error retrieving scan results</EmptyState.Title>
          <EmptyState.Info>{scanResultsError}</EmptyState.Info>
        </EmptyState>
      );
    }

    if (_.size(scanResults) === 0) {
      return (
        <EmptyState>
          <EmptyState.Icon name="warning-triangle-o" />
          <EmptyState.Title>
            {`${dictionary[status] || ''} systems were not available, please refresh.`}
          </EmptyState.Title>
        </EmptyState>
      );
    }

    return this.renderResults(scanResults);
  }
}

ScanHostList.propTypes = {
  scanId: PropTypes.number,
  sourceId: PropTypes.number,
  lastRefresh: PropTypes.number,
  status: PropTypes.string,
  renderHostRow: PropTypes.func,
  useConnectionResults: PropTypes.bool,
  useInspectionResults: PropTypes.bool,
  getConnectionScanResults: PropTypes.func,
  getInspectionScanResults: PropTypes.func
};

ScanHostList.defaultProps = {
  scanId: null,
  sourceId: null,
  lastRefresh: 0,
  status: null,
  renderHostRow: helpers.noop,
  useConnectionResults: false,
  useInspectionResults: false,
  getConnectionScanResults: helpers.noop,
  getInspectionScanResults: helpers.noop
};

const mapDispatchToProps = dispatch => ({
  getConnectionScanResults: (id, query) => dispatch(reduxActions.scans.getConnectionScanResults(id, query)),
  getInspectionScanResults: (id, query) => dispatch(reduxActions.scans.getInspectionScanResults(id, query))
});

const mapStateToProps = () => ({});

const ConnectedScanHostList = connect(
  mapStateToProps,
  mapDispatchToProps
)(ScanHostList);

export { ConnectedScanHostList as default, ConnectedScanHostList, ScanHostList };
